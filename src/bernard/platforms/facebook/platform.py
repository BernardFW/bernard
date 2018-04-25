# coding: utf-8

import asyncio
import hmac
import logging
from datetime import (
    tzinfo,
)
from hashlib import (
    sha1,
    sha256,
)
from textwrap import (
    wrap,
)
from typing import (
    Any,
    ByteString,
    Dict,
    List,
    Optional,
    Set,
    Text,
    Tuple,
)
from urllib.parse import (
    urljoin,
)

import aiohttp
import jwt
from aiohttp.web import (
    Request as HttpRequest,
)
from aiohttp.web_response import (
    Response,
    json_response,
)
from aiohttp.web_urldispatcher import (
    UrlDispatcher,
)
from dateutil import (
    tz,
)
from facepy import (
    SignedRequest,
    SignedRequestError,
)

import ujson
from bernard import (
    layers as lyr,
)
from bernard.conf import (
    settings,
)
from bernard.core.health_check import (
    HealthCheckFail,
)
from bernard.engine.platform import (
    PlatformOperationError,
    SimplePlatform,
)
from bernard.engine.request import (
    BaseMessage,
    Conversation,
    Request,
    User,
)
from bernard.engine.responder import (
    Responder,
)
from bernard.i18n.translator import (
    render,
)
from bernard.layers import (
    BaseLayer,
    Stack,
)
from bernard.layers.definitions import (
    BaseMediaLayer,
)
from bernard.media.base import (
    BaseMedia,
    UrlMedia,
)
from bernard.reporter import (
    reporter,
)
from bernard.utils import (
    dict_is_subset,
)

from .layers import (
    ButtonTemplate,
    GenericTemplate,
    MessagingType,
    OptIn,
    QuickRepliesList,
    QuickReply,
)

FB_API = '2.12'
MESSAGES_ENDPOINT = f'https://graph.facebook.com/v{FB_API}/me/messages'
PROFILE_ENDPOINT = f'https://graph.facebook.com/v{FB_API}/me/messenger_profile'
GRAPH_ENDPOINT = f'https://graph.facebook.com/v{FB_API}/{"{}"}'


logger = logging.getLogger('bernard.platform.facebook')


def sign_message(body: ByteString, secret: Text) -> Text:
    """
    Compute a message's signature.
    """

    return 'sha1={}'.format(
        hmac.new(secret.encode(), body, sha1).hexdigest()
    )


class FacebookUser(User):
    """
    That is the Facebook user class. So far it just computes the unique user
    ID.
    """

    def __init__(self,
                 fbid: Text,
                 page_id: Text,
                 facebook: 'Facebook',
                 message: 'FacebookMessage'):
        self.fbid = fbid
        self.page_id = page_id
        self.facebook = facebook
        self.message = message
        self._cache = None
        super(FacebookUser, self).__init__(self._fbid_to_id(fbid))

    def _fbid_to_id(self, fbid: Text):
        """
        Transforms a Facebook user ID into a unique user ID.
        """
        return 'facebook:user:{}'.format(fbid)

    async def _get_user(self):
        """
        Get the user dict from cache or query it from the platform if missing.
        """

        if self._cache is None:
            try:
                self._cache = \
                    await self.facebook.get_user(self.fbid, self.page_id)
            except PlatformOperationError:
                self._cache = {}
        return self._cache

    async def get_full_name(self) -> Text:
        """
        Let's implement this later
        """
        raise NotImplementedError

    async def get_formal_name(self) -> Text:
        """
        Let's implement this later
        """
        raise NotImplementedError

    async def get_friendly_name(self) -> Text:
        """
        The friendly name is mapped to Facebook's first name. If the first
        name is missing, use the last name.
        """
        u = await self._get_user()
        f = u.get('first_name', '').strip()
        l = u.get('last_name', '').strip()

        return f or l

    async def get_gender(self) -> User.Gender:
        """
        Get the gender from Facebook.
        """
        u = await self._get_user()

        try:
            return User.Gender(u.get('gender'))
        except ValueError:
            return User.Gender.unknown

    async def get_timezone(self) -> Optional[tzinfo]:
        """
        We can't exactly know the time zone of the user from what Facebook
        gives (fucking morons) but we can still give something that'll work
        until next DST.
        """

        u = await self._get_user()
        diff = float(u.get('timezone', 0)) * 3600.0

        return tz.tzoffset('ITC', diff)

    async def get_locale(self) -> Text:
        u = await self._get_user()
        return u.get('locale', '')


class FacebookConversation(Conversation):
    """
    That is a Facebook conversation. Some idea as the user.
    """

    def __init__(self, fbid: Text):
        self.fbid = fbid
        super(FacebookConversation, self).__init__(self._fbid_to_id(fbid))

    def _fbid_to_id(self, fbid: Text):
        """
        Facebook ID into conversation ID. So far we just handle user-to-bot
        cases, but who knows it might change in the future.
        """
        return 'facebook:conversation:user:{}'.format(fbid)


class FacebookMessage(BaseMessage):
    """
    Decodes the raw JSON sent by Facebook and allow to extract the user and the
    accompanying layers.
    """

    def __init__(self, event, facebook, confusing=True):
        self._event = event
        self._facebook = facebook
        self._confusing = confusing

    def get_platform(self) -> Text:
        """
        The platform is always Facebook
        """
        return 'facebook'

    def get_user(self) -> FacebookUser:
        """
        Generate a Facebook user instance
        """
        return FacebookUser(
            self._event['sender']['id'],
            self.get_page_id(),
            self._facebook,
            self,
        )

    def get_conversation(self) -> FacebookConversation:
        """
        Generate a Facebook conversation instance
        """
        return FacebookConversation(self._event['sender']['id'])

    def get_layers(self) -> List[BaseLayer]:
        """
        Return all layers that can be found in the message.
        """
        out = []
        msg = self._event.get('message', {})

        if 'text' in msg:
            out.append(lyr.RawText(msg['text']))

        for attachment in msg.get('attachments') or []:
            if attachment['type'] == 'image':
                out.append(lyr.Image(UrlMedia(attachment['payload']['url'])))
            elif attachment['type'] == 'audio':
                out.append(lyr.Audio(UrlMedia(attachment['payload']['url'])))
            elif attachment['type'] == 'file':
                out.append(lyr.File(UrlMedia(attachment['payload']['url'])))
            elif attachment['type'] == 'video':
                out.append(lyr.Video(UrlMedia(attachment['payload']['url'])))
            elif attachment['type'] == 'location':
                # noinspection PyArgumentList
                out.append(lyr.Location(lyr.Location.Point(
                    lat=attachment['payload']['coordinates']['lat'],
                    lon=attachment['payload']['coordinates']['long'],
                )))

        if 'quick_reply' in msg:
            out.append(QuickReply(msg['quick_reply']['payload']))

        if 'postback' in self._event:
            payload = ujson.loads(self._event['postback']['payload'])
            out.append(lyr.Postback(payload))

        if 'optin' in self._event:
            out.append(OptIn(self._event['optin']['ref']))

        return out

    def get_page_id(self) -> Text:
        """
        That's for internal use, extract the Facebook page ID.
        """
        return self._event['recipient']['id']

    def should_confuse(self) -> bool:
        """
        The message is marked confusing or not at init
        """
        return self._confusing

    async def get_token(self) -> Text:
        user = self.get_user()

        return jwt.encode(
            {
                'fb_psid': user.fbid,
                'fb_pid': user.page_id,
            },
            settings.WEBVIEW_SECRET_KEY,
            algorithm=settings.WEBVIEW_JWT_ALGORITHM,
        )


class FacebookResponder(Responder):
    """
    Not much to do here
    """


class Facebook(SimplePlatform):
    NAME = 'facebook'

    PATTERNS = {
        'text': '^(Text|RawText|MultiText)+ QuickRepliesList? MessagingType?$',
        'generic_template': '^GenericTemplate QuickRepliesList? '
                            'MessagingType?$',
        'button_template': '^ButtonTemplate QuickRepliesList? '
                           'MessagingType?$',
        'attachment': '^(Image|Audio|Video|File) QuickRepliesList? '
                      'MessagingType?$',
        'sleep': '^Sleep$',
        'typing': '^Typing$',
    }

    @classmethod
    async def self_check(cls):
        """
        Check that the configuration is correct

        - Presence of "BERNARD_BASE_URL" in the global configuration
        - Presence of a "WEBVIEW_SECRET_KEY"
        """

        async for check in super().self_check():
            yield check

        s = cls.settings()

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

    @property
    def app_access_token(self):
        """
        App token to access app configuration API
        """

        page = self.settings()
        return f"{page['app_id']}|{page['app_secret']}"

    @property
    def verify_token(self):
        """
        Automatically generated secure verify token
        """

        h = sha256()
        h.update(self.app_access_token.encode())
        return h.hexdigest()

    @property
    def webhook_path(self):
        """
        Path to the webhook
        """

        return f'/hooks/{self.id}'

    @property
    def webhook_url(self):
        """
        Full URL to the hook
        """

        return urljoin(settings.BERNARD_BASE_URL, self.webhook_path)

    def hook_up(self, router: UrlDispatcher):
        """
        Dynamically hooks the right webhook paths
        """

        router.add_get(self.webhook_path, self.check_hook)
        router.add_post(self.webhook_path, self.receive_events)

    async def check_hook(self, request: HttpRequest):
        """
        Called when Facebook checks the hook
        """

        verify_token = request.query.get('hub.verify_token')

        if not verify_token:
            return json_response({
                'error': 'No verification token was provided',
            }, status=400)

        if verify_token == self.verify_token:
            return Response(text=request.query.get('hub.challenge', ''))

        return json_response({
            'error': 'could not find the page token in the configuration',
        })

    async def receive_events(self, request: HttpRequest):
        """
        Events received from Facebook
        """

        body = await request.read()
        s = self.settings()

        try:
            content = ujson.loads(body)
        except ValueError:
            return json_response({
                'error': True,
                'message': 'Cannot decode body'
            }, status=400)

        secret = s['app_secret']
        actual_sig = request.headers['X-Hub-Signature']
        expected_sig = sign_message(body, secret)

        if not hmac.compare_digest(actual_sig, expected_sig):
            return json_response({
                'error': True,
                'message': 'Invalid signature',
            }, status=401)

        for entry in content['entry']:
            for raw_message in entry.get('messaging', []):
                message = FacebookMessage(raw_message, self)
                await self.handle_event(message)

        return json_response({
            'ok': True,
        })

    async def _deferred_init(self):
        """
        Run those things in a sepearate tasks as they are not required for the
        bot to work and they take a lot of time to run.
        """

        await self._check_subscriptions()
        await self._set_whitelist()
        await self._set_get_started()
        await self._set_greeting_text()
        await self._set_persistent_menu()

    async def _get_messenger_profile(self, page, fields: List[Text]):
        """
        Fetch the value of specified fields in order to avoid setting the same
        field twice at the same value (since Facebook engineers are not able
        to make menus that keep on working if set again).
        """

        params = {
            'access_token': page['page_token'],
            'fields': ','.join(fields),
        }

        get = self.session.get(PROFILE_ENDPOINT, params=params)
        async with get as r:
            await self._handle_fb_response(r)

            out = {}

            for data in (await r.json())['data']:
                out.update(data)

            return out

    async def _send_to_messenger_profile(self, page, content):
        """
        The messenger profile API handles all meta-information about the bot,
        like the menu. This allows to submit data to this API endpoint.

        :param page: page dict from the configuration
        :param content: content to be sent to Facebook (as dict)
        """

        log_name = ', '.join(repr(x) for x in content.keys())
        page_id = page['page_id']

        current = await self._get_messenger_profile(page, content.keys())

        if dict_is_subset(content, current):
            logger.info('Page %s: %s is already up to date', page_id, log_name)
            return

        params = {
            'access_token': page['page_token'],
        }

        headers = {
            'content-type': 'application/json',
        }

        post = self.session.post(
            PROFILE_ENDPOINT,
            params=params,
            headers=headers,
            data=ujson.dumps(content)
        )

        # noinspection PyBroadException
        try:
            async with post as r:
                await self._handle_fb_response(r)
        except Exception:
            logger.exception('Page %s: %s could not be set', page_id, log_name)
            reporter.report()
        else:
            logger.info('Page %s: %s was updated', page_id, log_name)

    async def _set_get_started(self):
        """
        Set the "get started" action for all configured pages.
        """

        page = self.settings()

        if 'get_started' in page:
            payload = page['get_started']
        else:
            payload = {'action': 'get_started'}

        await self._send_to_messenger_profile(page, {
            'get_started': {
                'payload': ujson.dumps(payload),
            },
        })

        logger.info('Get started set for page %s', page['page_id'])

    async def _set_greeting_text(self):
        """
        Set the greeting text of the page
        """

        page = self.settings()

        if 'greeting' in page:
            await self._send_to_messenger_profile(page, {
                'greeting': page['greeting'],
            })

            logger.info('Greeting text set for page %s', page['page_id'])

    async def _set_persistent_menu(self):
        """
        Define the persistent menu for all pages
        """

        page = self.settings()

        if 'menu' in page:
            await self._send_to_messenger_profile(page, {
                'persistent_menu': page['menu'],
            })

            logger.info('Set menu for page %s', page['page_id'])

    async def _set_whitelist(self):
        """
        Whitelist domains for the messenger extensions
        """

        page = self.settings()

        if 'whitelist' in page:
            await self._send_to_messenger_profile(page, {
                'whitelisted_domains': page['whitelist'],
            })

            logger.info('Whitelisted %s for page %s',
                        page['whitelist'],
                        page['page_id'])

    def _get_subscriptions_endpoint(self):
        """
        Generates the URL and tokens for the subscriptions endpoint
        """

        s = self.settings()

        params = {
            'access_token': self.app_access_token,
        }

        return (
            GRAPH_ENDPOINT.format(f'{s["app_id"]}/subscriptions'),
            params,
        )

    async def _get_subscriptions(self) -> Tuple[Set[Text], Text]:
        """
        List the subscriptions currently active
        """

        url, params = self._get_subscriptions_endpoint()

        get = self.session.get(url, params=params)

        async with get as r:
            await self._handle_fb_response(r)
            data = await r.json()

            for scope in data['data']:
                if scope['object'] == 'page':
                    return (
                        set(x['name'] for x in scope['fields']),
                        scope['callback_url'],
                    )

        return set(), ''

    async def _set_subscriptions(self, subscriptions):
        """
        Set the subscriptions to a specific list of values
        """

        url, params = self._get_subscriptions_endpoint()

        data = {
            'object': 'page',
            'callback_url': self.webhook_url,
            'fields': ', '.join(subscriptions),
            'verify_token': self.verify_token,
        }

        headers = {
            'Content-Type': 'application/json',
        }

        post = self.session.post(
            url,
            params=params,
            data=ujson.dumps(data),
            headers=headers,
        )

        async with post as r:
            await self._handle_fb_response(r)
            data = await r.json()

    async def _check_subscriptions(self):
        """
        Checks that all subscriptions are subscribed
        """

        subscribed, url = await self._get_subscriptions()
        expect = set(settings.FACEBOOK_SUBSCRIPTIONS)

        if (expect - subscribed) or url != self.webhook_url:
            await self._set_subscriptions(expect | subscribed)
            logger.info('Updated webhook subscriptions')
        else:
            logger.info('No need to update webhook subscriptions')

    async def handle_event(self, event: FacebookMessage):
        """
        Handle an incoming message from Facebook.
        """
        responder = FacebookResponder(self)
        await self._notify(event, responder)

    def _access_token(self, request: Request=None, page_id: Text=''):
        """
        Guess the access token for that specific request.
        """

        if not page_id:
            msg = request.message  # type: FacebookMessage
            page_id = msg.get_page_id()

        page = self.settings()

        if page['page_id'] == page_id:
            return page['page_token']

        raise PlatformOperationError('Trying to get access token of the '
                                     'page "{}", which is not configured.'
                                     .format(page_id))

    async def _make_qr(self,
                       qr: QuickRepliesList.BaseOption,
                       request: Request):
        """
        Generate a single quick reply's content.
        """

        if isinstance(qr, QuickRepliesList.TextOption):
            return {
                'content_type': 'text',
                'title': await render(qr.text, request),
                'payload': qr.slug,
            }
        elif isinstance(qr, QuickRepliesList.LocationOption):
            return {
                'content_type': 'location',
            }

    async def _add_qr(self, stack, msg, request):
        try:
            qr = stack.get_layer(QuickRepliesList)
        except KeyError:
            pass
        else:
            # noinspection PyUnresolvedReferences
            msg['quick_replies'] = [
                await self._make_qr(o, request) for o in qr.options
            ]

    async def _send_text(self, request: Request, stack: Stack):
        """
        Send text layers to the user. Each layer will go in its own bubble.

        Also, Facebook limits messages to 320 chars, so if any message is
        longer than that it will be split into as many messages as needed to
        be accepted by Facebook.
        """

        parts = []

        for layer in stack.layers:
            if isinstance(layer, lyr.MultiText):
                lines = await render(layer.text, request, multi_line=True)
                for line in lines:
                    for part in wrap(line, 320):
                        parts.append(part)
            elif isinstance(layer, (lyr.Text, lyr.RawText)):
                text = await render(layer.text, request)
                for part in wrap(text, 320):
                    parts.append(part)

        for part in parts[:-1]:
            await self._send(request, {
                'text': part,
            }, stack)

        part = parts[-1]

        msg = {
            'text': part,
        }

        await self._add_qr(stack, msg, request)
        await self._send(request, msg, stack)

    async def _send_generic_template(self, request: Request, stack: Stack):
        """
        Generates and send a generic template.
        """

        gt = stack.get_layer(GenericTemplate)
        payload = await gt.serialize(request)

        msg = {
            'attachment': {
                'type': 'template',
                'payload': payload
            }
        }

        await self._add_qr(stack, msg, request)
        await self._send(request, msg, stack)

    async def _send_button_template(self, request: Request, stack: Stack):
        """
        Generates and send a button template.
        """

        gt = stack.get_layer(ButtonTemplate)

        payload = {
            'template_type': 'button',
            'text': await render(gt.text, request),
            'buttons': [await b.serialize(request) for b in gt.buttons],
        }

        msg = {
            'attachment': {
                'type': 'template',
                'payload': payload
            }
        }

        await self._add_qr(stack, msg, request)
        await self._send(request, msg, stack)

    async def _send_attachment(self, request: Request, stack: Stack):
        types = {
            lyr.Image: 'image',
            lyr.Audio: 'audio',
            lyr.File: 'file',
            lyr.Video: 'video',
        }

        l: BaseMediaLayer = stack.layers[0]
        media = await self.ensure_usable_media(l.media)

        # noinspection PyTypeChecker
        msg = {
            'attachment': {
                'type': types[l.__class__],
                'payload': {
                    'url': media.url,
                }
            },
        }

        await self._add_qr(stack, msg, request)
        await self._send(request, msg, stack)

    async def _send_sleep(self, request: Request, stack: Stack):
        """
        Sleep for the amount of time specified in the Sleep layer
        """

        duration = stack.get_layer(lyr.Sleep).duration
        await asyncio.sleep(duration)

    async def _send_typing(self, request: Request, stack: Stack):
        """
        Send to Facebook typing indications
        """

        active = stack.get_layer(lyr.Typing).active

        msg = ujson.dumps({
            'recipient': {
                'id': request.conversation.fbid,
            },
            'sender_action': 'typing_on' if active else 'typing_off',
        })

        headers = {
            'content-type': 'application/json',
        }

        params = {
            'access_token': self._access_token(request),
        }

        post = self.session.post(
            MESSAGES_ENDPOINT,
            params=params,
            data=msg,
            headers=headers,
        )

        logger.debug('Sending: %s', msg)

        async with post as r:
            await self._handle_fb_response(r)

    async def _handle_fb_response(self, response: aiohttp.ClientResponse):
        """
        Check that Facebook was OK with the API call we just made and raise
        an exception if it failed.
        """

        ok = response.status == 200

        if not ok:
            # noinspection PyBroadException
            try:
                error = (await response.json())['error']['message']
            except Exception:
                error = '(nothing)'

            raise PlatformOperationError('Facebook says: "{}"'
                                         .format(error))

    async def _send(self,
                    request: Request,
                    content: Dict[Text, Any],
                    stack: Stack):
        """
        Actually proceed to sending the message to the Facebook API.
        """

        msg = {
            'recipient': {
                'id': request.conversation.fbid,
            },
            'message': content,
        }

        if stack and stack.has_layer(MessagingType):
            mt = stack.get_layer(MessagingType)
        else:
            mt = MessagingType(response=True)

        msg.update(mt.serialize())
        msg_json = ujson.dumps(msg)

        headers = {
            'content-type': 'application/json',
        }

        params = {
            'access_token': self._access_token(request),
        }

        post = self.session.post(
            MESSAGES_ENDPOINT,
            params=params,
            data=msg_json,
            headers=headers,
        )

        logger.debug('Sending: %s', msg_json)

        async with post as r:
            await self._handle_fb_response(r)

    async def get_user(self, user_id, page_id):
        """
        Query a user from the API and return its JSON
        """

        access_token = self._access_token(page_id=page_id)

        params = {
            'fields': 'first_name,last_name,profile_pic,locale,timezone'
                      ',gender',
            'access_token': access_token,
        }

        url = GRAPH_ENDPOINT.format(user_id)

        get = self.session.get(url, params=params)
        async with get as r:
            await self._handle_fb_response(r)
            return await r.json()

    async def ensure_usable_media(self, media: BaseMedia) -> UrlMedia:
        """
        So far, let's just accept URL media. We'll see in the future how it
        goes.
        """

        if not isinstance(media, UrlMedia):
            raise ValueError('Facebook platform only accepts URL media')

        return media

    def _make_fake_message(self, user_id, page_id, payload):
        """
        Creates a fake message for the given user_id. It contains a postback
        with the given payload.
        """

        event = {
            'sender': {
                'id': user_id,
            },
            'recipient': {
                'id': page_id,
            },
            'postback': {
                'payload': ujson.dumps(payload),
            },
        }

        return FacebookMessage(event, self, False)

    def _message_from_sr(self, token: Text, payload: Any) \
            -> Optional[BaseMessage]:
        """
        Tries to verify the signed request
        """

        page = self.settings()
        secret = page['app_secret']

        try:
            sr_data = SignedRequest.parse(token, secret)
        except (TypeError, ValueError, SignedRequestError) as e:
            return

        return self._make_fake_message(
            sr_data['psid'],
            page['page_id'],
            payload,
        )

    def _message_from_token(self, token: Text, payload: Any) \
            -> Optional[BaseMessage]:
        """
        Analyzes a signed token and generates the matching message
        """

        try:
            tk = jwt.decode(token, settings.WEBVIEW_SECRET_KEY)
        except jwt.InvalidTokenError:
            return

        try:
            user_id = tk['fb_psid']
            assert isinstance(user_id, Text)
            page_id = tk['fb_pid']
            assert isinstance(page_id, Text)
        except (KeyError, AssertionError):
            return

        if self.settings()['page_id'] == page_id:
            return self._make_fake_message(user_id, page_id, payload)

    async def message_from_token(self, token: Text, payload: Any) \
            -> Optional[BaseMessage]:
        """
        There is two ways of getting a FB user: either with a signed request or
        either with a platform token. Both are tried out.
        """

        methods = [
            self._message_from_sr,
            self._message_from_token,
        ]

        for method in methods:
            msg = method(token, payload)

            if msg:
                return msg

    async def inject_message(self, message: FacebookMessage) -> None:
        await self.handle_event(message)
