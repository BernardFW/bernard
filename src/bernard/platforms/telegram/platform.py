import logging
import ujson
import jwt
from datetime import tzinfo
from hashlib import sha256
from typing import Text, Any, Dict, List, Optional, Set
from urllib.parse import quote, urljoin

from asyncio import Lock

from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from aiohttp.web_urldispatcher import UrlDispatcher

from bernard.core.health_check import HealthCheckFail
from bernard.engine.platform import PlatformOperationError
from bernard.conf import settings
from bernard.engine.request import BaseMessage, Conversation, User, \
    Request as BernardRequest
from bernard.engine.responder import Responder, Layers
from bernard.i18n import render
from bernard.layers import BaseLayer, Stack
from bernard import layers as lyr
from bernard.media.base import BaseMedia
from bernard.utils import patch_dict, patch_qs
from ...platforms import SimplePlatform
from .layers import (
    AnswerCallbackQuery,
    Update,
    InlineQuery,
    AnswerInlineQuery,
    Reply,
    InlineMessage,
    BotCommand,
)
from ._utils import set_reply_markup

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
        if 'is_inline_query' in self._chat:
            return f'telegram:inline_query:{self._chat["id"]}'
        else:
            return f'telegram:conversation:{self._chat["id"]}'


class TelegramUser(User):
    def __init__(self, user, chat, telegram: 'Telegram'):
        self._user = user
        self._chat = chat
        self._telegram = telegram
        self._full_user = None
        self._lock = Lock()
        super(TelegramUser, self).__init__(self._make_id())

    def _make_id(self):
        return f'telegram:user:{self._user["id"]}'

    async def _get_full_user(self) -> Dict:
        """
        Sometimes Telegram does not provide all the user info with the message.
        In order to get the full profile (aka the language code) you need to
        call this method which will make sure that the full User object is
        loaded.

        The result is cached for the lifetime of the object, so if the function
        is called multiple times it will only fetch the user once. There is
        a locking mechanism around the cache to allow concurrent calls.
        """

        if 'language_code' in self._user:
            return self._user

        async with self._lock:
            if self._full_user is None:
                cm = await self._telegram.call(
                    'getChatMember',
                    user_id=self._user['id'],
                    chat_id=self._chat['id'],
                )
                self._full_user = cm['result']['user']

            return self._full_user

    async def get_friendly_name(self) -> Text:
        return self._user.get('first_name')

    async def get_locale(self) -> Text:
        user = await self._get_full_user()
        return user.get('language_code', None)

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

    async def get_postback_url(self):
        """
        Generate a postback URL for Telegram.
        """

        content = {
            'user_id': self.id,
            'telegram_user_id': self._user['id'],
            'telegram_chat_id': self._chat['id'],
        }

        token = jwt.encode(
            content,
            settings.WEBVIEW_SECRET_KEY,
            algorithm=settings.WEBVIEW_JWT_ALGORITHM,
        )

        url = patch_qs(
            urljoin(settings.BERNARD_BASE_URL, '/postback/telegram'),
            {'token': token},
        )

        return url


class TelegramMessage(BaseMessage):
    def __init__(self, update: Dict, telegram: 'Telegram'):
        self._update = update
        self._telegram = telegram

    def get_layers(self) -> List[BaseLayer]:
        out = []

        if 'message' in self._update:
            msg = self._update.get('message', {})

            if 'text' in msg:
                text = msg['text']
                out.append(lyr.RawText(text))

                for entity in (msg.get('entities') or []):
                    o = entity['offset']
                    l = entity['length']
                    entity_text = text[o:o + l]

                    if entity['type'] == 'bot_command':
                        out.append(BotCommand(entity_text))

            if 'reply_to_message' in msg:
                sub_msg = TelegramMessage(
                    {'message': msg['reply_to_message']},
                    self._telegram,
                )
                out.append(lyr.Message(sub_msg))

        if 'callback_query' in self._update:
            payload = self._update['callback_query']['data']
            out.append(lyr.Postback(ujson.loads(payload)))
            out.append(InlineMessage())

            sub_msg = TelegramMessage(
                self._update['callback_query'],
                self._telegram,
            )
            out.append(lyr.Message(sub_msg))

        if 'inline_query' in self._update:
            out.append(InlineQuery(self._update['inline_query']))

        return out

    def get_platform(self) -> Text:
        return self._telegram.NAME

    def _get_chat(self) -> Dict:
        """
        As Telegram changes where the chat object is located in the response,
        this method tries to be smart about finding it in the right place.
        """

        if 'callback_query' in self._update:
            query = self._update['callback_query']
            if 'message' in query:
                return query['message']['chat']
            else:
                return {'id': query['chat_instance']}
        elif 'inline_query' in self._update:
            return patch_dict(
                self._update['inline_query']['from'],
                is_inline_query=True,
            )
        elif 'message' in self._update:
            return self._update['message']['chat']

    def _get_user(self) -> Dict:
        """
        Same thing as for `_get_chat()` but for the user related to the
        message.
        """

        if 'callback_query' in self._update:
            return self._update['callback_query']['from']
        elif 'inline_query' in self._update:
            return self._update['inline_query']['from']
        elif 'message' in self._update:
            return self._update['message']['from']

    def get_conversation(self) -> Conversation:
        return TelegramConversation(self._get_chat())

    def get_user(self) -> User:
        return TelegramUser(self._get_user(), self._get_chat(), self._telegram)

    def get_chat_id(self) -> Text:
        return self._get_chat()['id']


class TelegramResponder(Responder):
    """
    This responder handles most of the magic behind Telegram messages
    acknowledgements and so on.
    """

    def __init__(self, update, platform):
        super(TelegramResponder, self).__init__(platform)

        self._update = update

        if 'callback_query' in update:
            self._acq = AnswerCallbackQuery()
        else:
            self._acq = None

    def send(self, stack: Layers):
        """
        Intercept any potential "AnswerCallbackQuery" before adding the stack
        to the output buffer.
        """

        if not isinstance(stack, Stack):
            stack = Stack(stack)

        if 'callback_query' in self._update and stack.has_layer(Update):
            layer = stack.get_layer(Update)

            try:
                msg = self._update['callback_query']['message']
            except KeyError:
                layer.inline_message_id = \
                    self._update['callback_query']['inline_message_id']
            else:
                layer.chat_id = msg['chat']['id']
                layer.message_id = msg['message_id']

        if stack.has_layer(AnswerCallbackQuery):
            self._acq = stack.get_layer(AnswerCallbackQuery)
            stack = Stack([
                l for l in stack.layers
                if not isinstance(l, AnswerCallbackQuery)
            ])

        if stack.has_layer(Reply):
            layer = stack.get_layer(Reply)

            if 'message' in self._update:
                layer.message = self._update['message']
            elif 'callback_query' in self._update:
                layer.message = self._update['callback_query']['message']

        if 'inline_query' in self._update \
                and stack.has_layer(AnswerInlineQuery):
            a = stack.get_layer(AnswerInlineQuery)
            a.inline_query_id = self._update['inline_query']['id']

        if stack.layers:
            return super(TelegramResponder, self).send(stack)

    async def flush(self, request: BernardRequest):
        """
        If there's a AnswerCallbackQuery scheduled for reply, place the call
        before actually flushing the buffer.
        """

        if self._acq and 'callback_query' in self._update:
            try:
                cbq_id = self._update['callback_query']['id']
            except KeyError:
                pass
            else:
                await self.platform.call(
                    'answerCallbackQuery',
                    **(await self._acq.serialize(cbq_id))
                )

        return await super(TelegramResponder, self).flush(request)


class Telegram(SimplePlatform):
    NAME = 'telegram'
    PATTERNS = {
        'plain_text': '^(Text|RawText)+ '
                      '(InlineKeyboard|ReplyKeyboard|ReplyKeyboardRemove)? '
                      'Reply?$'

                      '|^(Text|RawText) InlineKeyboard? Reply? Update$',
        'inline_answer': '^AnswerInlineQuery$',
        'markdown': '^Markdown+ '
                    '(InlineKeyboard|ReplyKeyboard|ReplyKeyboardRemove)? '
                    'Reply?$'

                    '|^Markdown InlineKeyboard? Reply? Update$',
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

        if not hasattr(settings, 'WEBVIEW_SECRET_KEY'):
            yield HealthCheckFail(
                '00005',
                '"WEBVIEW_SECRET_KEY" cannot be found in the configuration. '
                'It is required in order to be able to create secure postback '
                'URLs.'
            )

    def hook_up(self, router: UrlDispatcher):
        router.add_post(self.make_hook_path(), self.receive_updates)
        router.add_post('/postback/telegram', self.receive_postback)

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

        logger.debug('Received from Telegram: %s', content)

        message = TelegramMessage(content, self)
        responder = TelegramResponder(content, self)
        await self._notify(message, responder)

        return json_response({
            'error': False,
        })

    async def receive_postback(self, request: Request):
        """
        Handle postbacks. A fake Telegram message will be generated and fed to
        the normal process.

        Since postback messages need to be acknowledged in Telegram, the ID
        is voluntarily not set so the Responder knows it's a fake message and
        thus needs no acknowledgement.
        """

        tk = request.query.get('token')

        if not tk:
            return json_response({
                'error': True,
                'message': 'Missing "{}"'.format('token'),
            }, status=400)

        try:
            tk = jwt.decode(tk, settings.WEBVIEW_SECRET_KEY)
        except jwt.InvalidTokenError:
            return json_response({
                'error': True,
                'message': 'Provided token is invalid'
            }, status=400)

        try:
            user_id = tk['telegram_user_id']
            assert isinstance(user_id, int)
            chat_id = tk['telegram_chat_id']
            assert isinstance(chat_id, int)
        except (KeyError, AssertionError):
            return json_response({
                'error': True,
                'message': 'Provided payload is invalid'
            }, status=400)

        body = await request.read()

        try:
            ujson.loads(body)
        except ValueError:
            return json_response({
                'error': True,
                'message': 'Cannot decode body',
            }, status=400)

        fake_message = {
            'callback_query': {
                'from': {
                    'id': user_id,
                },
                'message': {
                    'chat': {
                        'id': chat_id,
                    },
                },
                'data': body,
            }
        }

        message = TelegramMessage(fake_message, self)
        responder = TelegramResponder(fake_message, self)
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

    async def call(self,
                   method: Text,
                   _ignore: Set[Text] = None,
                   **params: Dict[Text, Any]):
        """
        Call a telegram method

        :param _ignore: List of reasons to ignore
        :param method: Name of the method to call
        :param params: Dictionary of the parameters to send

        :return: Returns the API response
        """

        logger.debug('Calling Telegram %s(%s)', method, params)

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
            out = await self._handle_telegram_response(r, _ignore)
            logger.debug('Telegram replied: %s', out)
            return out

    async def _handle_telegram_response(self, response, ignore=None):
        """
        Parse a response from Telegram. If there's an error, an exception will
        be raised with an explicative message.

        :param response: Response to parse
        :return: Data
        """

        if ignore is None:
            ignore = set()

        ok = response.status == 200

        try:
            data = await response.json()

            if not ok:
                desc = data['description']

                if desc in ignore:
                    return

                raise PlatformOperationError(
                    'Telegram replied with an error: {}'
                    .format(desc)
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

    async def _send_text(self,
                         request: Request,
                         stack: Stack,
                         parse_mode: Optional[Text] = None):
        """
        Base function for sending text
        """

        parts = []
        chat_id = request.message.get_chat_id()

        for layer in stack.layers:
            if isinstance(layer, (lyr.Text, lyr.RawText, lyr.Markdown)):
                text = await render(layer.text, request)
                parts.append(text)

        for part in parts[:-1]:
            await self.call(
                'sendMessage',
                text=part,
                chat_id=chat_id,
            )

        msg = {
            'text': parts[-1],
            'chat_id': chat_id,
        }

        if parse_mode is not None:
            msg['parse_mode'] = parse_mode

        await set_reply_markup(msg, request, stack)

        if stack.has_layer(Reply):
            reply = stack.get_layer(Reply)
            if reply.message:
                msg['reply_to_message_id'] = reply.message['message_id']

        if stack.has_layer(Update):
            update = stack.get_layer(Update)

            if update.inline_message_id:
                msg['inline_message_id'] = update.inline_message_id
                del msg['chat_id']
            else:
                msg['message_id'] = update.message_id

            await self.call(
                'editMessageText',
                {'Bad Request: message is not modified'},
                **msg
            )
        else:
            await self.call('sendMessage', **msg)

    async def _send_plain_text(self, request: Request, stack: Stack):
        """
        Sends plain text using `_send_text()`.
        """

        await self._send_text(request, stack, None)

    async def _send_markdown(self, request: Request, stack: Stack):
        """
        Sends Markdown using `_send_text()`
        """

        await self._send_text(request, stack, 'Markdown')

    async def _send_inline_answer(self, request: Request, stack: Stack):
        aiq = stack.get_layer(AnswerInlineQuery)
        answer = await aiq.serialize(request)
        await self.call('answerInlineQuery', **answer)

    def ensure_usable_media(self, media: BaseMedia) -> BaseMedia:
        raise NotImplementedError
