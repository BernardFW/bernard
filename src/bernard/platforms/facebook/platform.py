# coding: utf-8

import aiohttp
import asyncio
import ujson
import logging
import jwt
from textwrap import wrap
from typing import Text, List, Any, Dict, Optional
from urllib.parse import urljoin

from bernard.reporter import reporter
from bernard.utils import patch_qs, dict_is_subset
from dateutil import tz
from datetime import tzinfo
from bernard.engine.responder import Responder
from bernard.engine.request import Request, BaseMessage, User, Conversation
from bernard.i18n.translator import render
from bernard.layers import Stack, BaseLayer
from bernard import layers as lyr
from bernard.engine.platform import PlatformOperationError, SimplePlatform
from bernard.layers.definitions import BaseMediaLayer
from bernard.media.base import BaseMedia, UrlMedia
from bernard.conf import settings

from .layers import MessagingType


MESSAGES_ENDPOINT = 'https://graph.facebook.com/v2.6/me/messages'
PROFILE_ENDPOINT = 'https://graph.facebook.com/v2.6/me/messenger_profile'
USER_ENDPOINT = 'https://graph.facebook.com/v2.6/{}'


logger = logging.getLogger('bernard.platform.facebook')


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

    async def get_postback_url(self) -> Text:
        content = {
            'user_id': self.id,
            'fb_psid': self.fbid,
            'fb_pid': self.page_id,
        }

        token = jwt.encode(
            content,
            settings.WEBVIEW_SECRET_KEY,
            algorithm=settings.WEBVIEW_JWT_ALGORITHM,
        )

        url = patch_qs(
            urljoin(self.message.get_url_base(), '/postback/facebook'),
            {'token': token}
        )

        return url


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
            out.append(lyr.QuickReply(msg['quick_reply']['payload']))

        if 'postback' in self._event:
            payload = ujson.loads(self._event['postback']['payload'])
            out.append(lyr.Postback(payload))

        if 'link_click' in self._event:
            out.append(lyr.LinkClick(
                self._event['link_click']['url'],
                self._event['link_click']['slug'],
            ))

        if 'close_webview' in self._event:
            out.append(lyr.CloseWebview(
                self._event['close_webview']['slug'],
            ))

        if 'optin' in self._event:
            out.append(lyr.OptIn(self._event['optin']['ref']))

        return out

    def get_page_id(self) -> Text:
        """
        That's for internal use, extract the Facebook page ID.
        """
        return self._event['recipient']['id']

    def get_url_base(self) -> Optional[Text]:
        """
        If available, return the URL base
        """
        url : Text = self._event.get('url_base')

        if url and url.startswith('http://'):
            url = 'https://' + url[7:]

        return url

    def should_confuse(self) -> bool:
        """
        The message is marked confusing or not at init
        """
        return self._confusing


class FacebookResponder(Responder):
    """
    Not much to do here
    """


class Facebook(SimplePlatform):
    NAME = 'facebook'

    PATTERNS = {
        'text': '^(Text|RawText|MultiText)+ QuickRepliesList? MessagingType?$',
        'generic_template': '^FbGenericTemplate QuickRepliesList? '
                            'MessagingType?$',
        'button_template': '^FbButtonTemplate QuickRepliesList? '
                           'MessagingType?$',
        'attachment': '^(Image|Audio|Video|File) QuickRepliesList? '
                      'MessagingType?$',
        'sleep': '^Sleep$',
        'typing': '^Typing$',
    }

    async def _deferred_init(self):
        """
        Run those things in a sepearate tasks as they are not required for the
        bot to work and they take a lot of time to run.
        """

        await self._set_get_started()
        await self._set_greeting_text()
        await self._set_persistent_menu()
        await self._set_whitelist()

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

        for page in self.settings():
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

        for page in self.settings():
            if 'greeting' in page:
                await self._send_to_messenger_profile(page, {
                    'greeting': page['greeting'],
                })

                logger.info('Greeting text set for page %s', page['page_id'])

    async def _set_persistent_menu(self):
        """
        Define the persistent menu for all pages
        """

        for page in self.settings():
            if 'menu' in page:
                await self._send_to_messenger_profile(page, {
                    'persistent_menu': page['menu'],
                })

                logger.info('Set menu for page %s', page['page_id'])

    async def _set_whitelist(self):
        """
        Whitelist domains for the messenger extensions
        """

        for page in self.settings():
            if 'whitelist' in page:
                await self._send_to_messenger_profile(page, {
                    'whitelisted_domains': page['whitelist'],
                })

                logger.info('Whitelisted %s for page %s',
                            page['whitelist'],
                            page['page_id'])

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

        for page in self.settings():
            if page['page_id'] == page_id:
                return page['page_token']

        raise PlatformOperationError('Trying to get access token of the '
                                     'page "{}", which is not configured.'
                                     .format(page_id))

    async def _make_qr(self,
                       qr: lyr.QuickRepliesList.BaseOption,
                       request: Request):
        """
        Generate a single quick reply's content.
        """

        if isinstance(qr, lyr.QuickRepliesList.TextOption):
            return {
                'content_type': 'text',
                'title': await render(qr.text, request),
                'payload': qr.slug,
            }
        elif isinstance(qr, lyr.QuickRepliesList.LocationOption):
            return {
                'content_type': 'location',
            }

    async def _add_qr(self, stack, msg, request):
        try:
            qr = stack.get_layer(lyr.QuickRepliesList)
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

        gt = stack.get_layer(lyr.FbGenericTemplate)
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

        gt = stack.get_layer(lyr.FbButtonTemplate)

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

        url = USER_ENDPOINT.format(user_id)

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
