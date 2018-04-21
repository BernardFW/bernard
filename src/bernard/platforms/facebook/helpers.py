# coding: utf-8
from enum import (
    Enum,
)
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Text,
)
from urllib.parse import (
    urljoin,
)

import jwt

import ujson
from bernard.conf import (
    settings,
)
from bernard.i18n import (
    TransText,
    render,
)
from bernard.media.base import (
    BaseMedia,
    UrlMedia,
)
from bernard.utils import (
    patch_qs,
)

if TYPE_CHECKING:
    from bernard.engine.request import Request
    from bernard.engine.platform import Platform
    from .layers import GenericTemplate


class WebviewRatio(Enum):
    """
    Different sizes you can open webviews at.
    """
    full = 'full'
    tall = 'tall'
    compact = 'compact'


class BaseButton(object):
    """
    Base utility class and interface for Facebook buttons.
    """
    def __init__(self, title: Text):
        self.title = title

    def __eq__(self, other):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError

    async def serialize(self, request: 'Request') -> Dict:
        """
        Transforms the object into a JSON-serializable structure
        """
        raise NotImplementedError

    def is_sharable(self):
        """
        Returns True if the button holds no sensitive (aka authentication)
        information. If it has, it will automatically disable the shareability
        of the template that holds that button.
        """
        return True


class UrlButton(BaseButton):
    """
    That's an URL button. It has quite a lot of options, see the init doc.
    """
    def __init__(self,
                 title: TransText,
                 url: Text,
                 sign_webview: bool=False,
                 webview_height_ratio: Optional[WebviewRatio]=None,
                 messenger_extensions: Optional[bool]=None,
                 fallback_url: Optional[Text]=None,
                 hide_share: Optional[bool]=None):
        """
        Please refer to the FB doc for more info.

        :param title: Title that will be displayed
        :param url: URL to send the user to
        :param sign_webview: Hash-sign the URL. This automatically disables the
                             sharing features. See the `bernard.js`
                             documentation for more information.
        :param webview_height_ratio: Displayed webview aspect ratio
        :param messenger_extensions: Enable messenger extensions
        :param fallback_url: If and ONLY if you enabled messenger extensions,
                             this URL is the URL to send to if the extensions
                             are not supported by the platform.
        :param hide_share: Hide the share button on the webview.
        """
        super().__init__(title)
        self.url = url
        self.sign_webview = sign_webview
        self.webview_height_ratio = webview_height_ratio
        self.messenger_extensions = messenger_extensions
        self.fallback_url = fallback_url
        self.hide_share = hide_share

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.url == other.url and
                self.sign_webview == other.sign_webview and
                self.webview_height_ratio == other.webview_height_ratio and
                self.messenger_extensions == other.messenger_exteions and
                self.fallback_url == other.fallback_url and
                self.hide_share == other.hide_share)

    def __repr__(self):
        return 'Url({}, {})'.format(repr(self.title), repr(self.url))

    async def _make_url(self, url: Text, request: 'Request') -> Text:
        """
        Signs the URL if needed
        """

        if self.sign_webview:
            return await request.sign_url(url)

        return url

    async def serialize(self, request: 'Request') -> Dict:
        out = {
            'type': 'web_url',
            'title': await render(self.title, request),
            'url': await self._make_url(self.url, request),
        }

        if self.webview_height_ratio is not None:
            out['webview_height_ratio'] = self.webview_height_ratio.value

        if self.messenger_extensions is not None:
            out['messenger_extensions'] = self.messenger_extensions

        if self.fallback_url is not None:
            out['fallback_url'] = \
                self._make_url(self.fallback_url, request)

        if self.hide_share or self.sign_webview:
            out['webview_share_button'] = 'hide'

        return out

    def is_sharable(self):
        """
        This button can be shared only if it is naive, eg it does not track
        URLs and does not embed an auto-connect code.
        """
        return not self.sign_webview


class PostbackButton(BaseButton):
    """
    That's a Facebook Postback button. When the user clicks on it, the FSM
    receives a Postback layer with the specified payload.
    """

    def __init__(self, title: TransText, payload: Any):
        super().__init__(title)
        self.payload = payload

    async def serialize(self, request: 'Request'):
        return {
            'type': 'postback',
            'title': await render(self.title, request),
            'payload': ujson.dumps(self.payload),
        }

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.payload == other.payload)

    def __repr__(self):
        return 'Postback({}, {})'.format(repr(self.title), repr(self.payload))


class CallButton(BaseButton):
    """
    A button to trigger a phone call. The phone number must be in the format
    "+123456789"
    """

    def __init__(self, title: TransText, phone_number: Text):
        super().__init__(title)
        self.phone_number = phone_number

    async def serialize(self, request: 'Request'):
        return {
            'type': 'phone_number',
            'title': await render(self.title, request),
            'payload': self.phone_number,
        }

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.phone_number == other.phone_number)

    def __repr__(self):
        return 'Postback({}, {})'\
            .format(repr(self.title), repr(self.phone_number))


class CardAction(UrlButton):
    """
    That is a simili-button that behaves like a URL button when the user clicks
    on a card.
    """

    def __init__(self,
                 url: Text,
                 sign_webview: bool=False,
                 webview_height_ratio: Optional[WebviewRatio]=None,
                 messenger_extensions: Optional[bool]=None,
                 fallback_url: Optional[Text]=None,
                 hide_share: Optional[bool]=None):
        super(CardAction, self).__init__(
            '', url, sign_webview, webview_height_ratio,
            messenger_extensions, fallback_url, hide_share
        )

    def __repr__(self):
        return 'CardAction({})'.format(repr(self.url))

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.url == other.url
            and self.sign_webview == other.sign_webview
            and self.webview_height_ratio == other.webview_height_ratio
            and self.messenger_extensions == other.messenger_extensions
            and self.fallback_url == other.fallback_url
            and self.hide_share == other.hide_share
        )

    async def serialize(self, request: 'Request'):
        out = await super().serialize(request)
        del out['title']
        return out


class Card(object):
    """
    A Facebook Card for the Generic Template.
    """
    def __init__(self,
                 title: TransText,
                 subtitle: Optional[TransText]=None,
                 buttons: Optional[List[BaseButton]]=None,
                 image: Optional[BaseMedia]=None,
                 default_action: Optional[CardAction]=None):
        self.title = title
        self.subtitle = subtitle
        self.buttons = buttons
        self.image = image
        self.default_action = default_action

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.title == other.title and
                self.subtitle == other.subtitle and
                list(self.buttons) == list(other.buttons) and
                self.image == other.image and
                self.default_action == other.default_action)

    def __repr__(self):
        return 'Card({})'.format(repr(self.title))

    async def convert_media(self, platform: 'Platform'):
        if self.image:
            self.image = await platform.ensure_usable_media(self.image)

    async def serialize(self, request: 'Request'):
        out = {
            'title': await render(self.title, request)
        }

        if self.subtitle:
            out['subtitle'] = await render(self.subtitle, request)

        if self.image:
            assert isinstance(self.image, UrlMedia)
            out['image_url'] = self.image.url

        if self.buttons:
            out['buttons'] = [await b.serialize(request) for b in self.buttons]

        if self.default_action:
            out['default_action'] = \
                self.default_action.serialize(request)

        return out

    def is_sharable(self):
        """
        Make sure that nothing inside blocks sharing.
        """
        if self.buttons:
            return (all(b.is_sharable() for b in self.buttons) and
                    self.default_action and
                    self.default_action.is_sharable())


class ShareButton(BaseButton):
    """
    That's a Facebook Share button. When the user clicks on it, the FbCard
    is share to an other user who can go to the bot.

    Parameter share_content define what will be share and must be a generic
    template.
    """

    def __init__(self, share_content: Optional['GenericTemplate'] = None):
        super().__init__('')
        self.share_content = share_content

    async def serialize(self, request: 'Request'):
        out = {
            'type': 'element_share'
        }

        if self.share_content:
            out['share_contents'] = {
                'attachment': {
                    'type': 'template',
                    'payload': await self.share_content.serialize(request),
                }
            }

        return out

    def __eq__(self, other):
        return (self.__class__ == other.__class__
                and self.share_content == other.share_content)

    def __repr__(self):
        return 'FbShareButton()'
