import logging
import ujson
from datetime import tzinfo
from hashlib import sha256
from typing import Text, Any, Dict, List, Optional
from urllib.parse import quote, urljoin

from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from aiohttp.web_urldispatcher import UrlDispatcher

from bernard.core.health_check import HealthCheckFail
from bernard.engine.platform import PlatformOperationError
from bernard.conf import settings
from bernard.engine.request import BaseMessage, Conversation, User
from bernard.engine.responder import Responder
from bernard.i18n import render
from bernard.layers import BaseLayer, Stack
from bernard import layers as lyr
from bernard.media.base import BaseMedia
from ...platforms import SimplePlatform


TELEGRAM_URL = 'https://api.telegram.org/bot{token}/{method}'

logger = logging.getLogger('bernard.platform.telegram')


class TelegramConversation(Conversation):
    """
    Matches the Telegram "chat" concept
    """

    def __init__(self, chat):
        self._chat = chat
        super(TelegramConversation, self).__init__(self._make_id())

    def _make_id(self):
        return f'telegram:conversation:{self._chat["id"]}'


class TelegramUser(User):
    def __init__(self, user):
        self._user = user
        super(TelegramUser, self).__init__(self._make_id())

    def _make_id(self):
        return f'telegram:user:{self._user["id"]}'

    async def get_friendly_name(self) -> Text:
        return self._user.get('first_name')

    async def get_locale(self) -> Text:
        return self._user.get('language_code', None)

    async def get_formal_name(self) -> Text:
        parts = [
            self._user.get('first_name'),
            self._user.get('last_name'),
        ]

        return ' '.join(x for x in parts if x)

    async def get_timezone(self) -> Optional[tzinfo]:
        return None

    async def get_full_name(self) -> Text:
        return await self.get_formal_name()


class TelegramMessage(BaseMessage):
    def __init__(self, update: Dict, telegram: 'Telegram'):
        self._update = update
        self._telegram = telegram

    def get_layers(self) -> List[BaseLayer]:
        # TODO create a MarkdownText layer

        out = []
        msg = self._update.get('message', {})

        if 'text' in msg:
            out.append(lyr.RawText(msg['text']))

        return out

    def get_platform(self) -> Text:
        return self._telegram.NAME

    def get_conversation(self) -> Conversation:
        return TelegramConversation(self._update['message']['chat'])

    def get_user(self) -> User:
        return TelegramUser(self._update['message']['from'])

    def get_chat_id(self) -> Text:
        return self._update['message']['chat']['id']


class TelegramResponder(Responder):
    pass


class Telegram(SimplePlatform):
    NAME = 'telegram'
    PATTERNS = {
        'plain_text': '(Text|RawText)+',
    }

    @classmethod
    async def self_check(cls):
        """
        Check that the configuration is correct

        - Presence of "token" in the settings
        - Presence of "BERNARD_BASE_URL" in the global configuration
        """

        # noinspection PyTypeChecker
        async for check in super(Telegram, cls).self_check():
            yield check

        s = cls.settings()

        try:
            assert isinstance(s['token'], str)
        except (KeyError, TypeError, AssertionError):
            yield HealthCheckFail(
                '00005',
                'Missing "token" for Telegram platform. You can obtain one by'
                'registering your bot in Telegram.',
            )

        if not hasattr(settings, 'BERNARD_BASE_URL'):
            yield HealthCheckFail(
                '00005',
                '"BERNARD_BASE_URL" cannot be found in the configuration. The'
                'Telegram platform needs it because it uses it to '
                'automatically register its hook.'
            )

    def hook_up(self, router: UrlDispatcher):
        router.add_post(self.make_hook_path(), self.receive_updates)

    async def receive_updates(self, request: Request):
        """
        Handle updates from Telegram
        """

        body = await request.read()

        try:
            content = ujson.loads(body)
        except ValueError:
            return json_response({
                'error': True,
                'message': 'Cannot decode body',
            }, status=400)

        message = TelegramMessage(content, self)
        responder = TelegramResponder(self)
        await self._notify(message, responder)

        return json_response({
            'error': False,
        })

    def make_url(self, method):
        """
        Generate a Telegram URL for this bot.
        """

        token = self.settings()['token']

        return TELEGRAM_URL.format(
            token=quote(token),
            method=quote(method),
        )

    async def call(self, method: Text, **params: Dict[Text, Any]):
        """
        Call a telegram method

        :param method: Name of the method to call
        :param params: Dictionary of the parameters to send

        :return: Returns the API response
        """

        url = self.make_url(method)

        headers = {
            'content-type': 'application/json',
        }

        post = self.session.post(
            url,
            data=ujson.dumps(params),
            headers=headers,
        )

        async with post as r:
            return await self._handle_telegram_response(r)

    async def _handle_telegram_response(self, response):
        """
        Parse a response from Telegram. If there's an error, an exception will
        be raised with an explicative message.

        :param response: Response to parse
        :return: Data
        """

        ok = response.status == 200

        try:
            data = await response.json()

            if not ok:
                raise PlatformOperationError(
                    'Telegram replied with an error: {}'
                    .format(data['description'])
                )
        except (ValueError, TypeError, KeyError):
            raise PlatformOperationError('An unknown Telegram error occurred')

        return data

    def make_hook_path(self):
        """
        Compute the path to the hook URL
        """

        token = self.settings()['token']
        h = sha256()
        h.update(token.encode())
        key = str(h.hexdigest())
        return f'/hooks/telegram/{key}'

    async def _deferred_init(self):
        """
        Register the web hook onto which Telegram should send its messages.
        """

        hook_path = self.make_hook_path()
        url = urljoin(settings.BERNARD_BASE_URL, hook_path)
        await self.call('setWebhook', url=url)
        logger.info('Setting Telegram webhook to "%s"', url)

    async def _send_plain_text(self, request: Request, stack: Stack):
        """
        Sends a plain text message
        """

        # TODO escape Markdown

        parts = []

        for layer in stack.layers:
            if isinstance(layer, (lyr.Text, lyr.RawText)):
                text = await render(layer.text, request)
                parts.append(text)

        for part in parts:
            await self.call(
                'sendMessage',
                text=part,
                chat_id=request.message.get_chat_id(),
            )

    def ensure_usable_media(self, media: BaseMedia) -> BaseMedia:
        raise NotImplementedError
