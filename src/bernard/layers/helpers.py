# coding: utf-8
import jwt
import ujson
from typing import Text, Optional, Dict, TYPE_CHECKING, Any, List
from enum import Enum
from bernard.conf import settings
from bernard.i18n import TransText, render
from bernard.media.base import BaseMedia, UrlMedia
from bernard.utils import patch_qs

if TYPE_CHECKING:
    from bernard.engine.request import Request
    from bernard.engine.platform import Platform


class FbWebviewRatio(Enum):
    """
    Different sizes you can open webviews at.
    """
    full = 'full'
    tall = 'tall'
    compact = 'compact'


class FbBaseButton(object):
    """
    Base utility class and interface for Facebook buttons.
    """
    def __init__(self, title: Text):
        self.title = title

    def __eq__(self, other):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError

    def serialize(self, request: 'Request') -> Dict:
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


class FbUrlButton(FbBaseButton):
    """
    That's an URL button. It has quite a lot of options, see the init doc.
    """
    def __init__(self,
                 title: TransText,
                 url: Text,
                 sign_webview: bool=False,
                 webview_height_ratio: Optional[FbWebviewRatio]=None,
                 messenger_extensions: Optional[bool]=None,
                 fallback_url: Optional[Text]=None,
                 hide_share: Optional[bool]=None):
        """
        Please refer to the FB doc for more info.
        
        TODO write some more detailed doc about `sign_webview`.

        :param title: Title that will be displayed
        :param url: URL to send the user to
        :param sign_webview: Add a JSON Web Token to the URL with the user ID
                             inside. You can do this if you want to auto-log
                             your user (provided that you extract the data
                             server-side, of course).
        :param webview_height_ratio: Displayed webview aspect ratio
        :param messenger_extensions: Enable messenger extensions
        :param fallback_url: If and ONLY if you enabled messenger extensions,
                             this URL is the URL to send to if the extensions
                             are not supported by the platform.
        :param hide_share: Hide the share button on the webview.
        """
        super(FbUrlButton, self).__init__(title)
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

    def serialize(self, request: 'Request') -> Dict:
        if self.sign_webview:
            user = request.user
            extra_qs = {
                settings.WEBVIEW_TOKEN_KEY: jwt.encode(
                    {
                        'user_id': user.id,
                    },
                    settings.WEBVIEW_SECRET_KEY,
                    algorithm=settings.WEBVIEW_JWT_ALGORITHM,
                )
            }
        else:
            extra_qs = {}

        out = {
            'type': 'web_url',
            'title': render(self.title, request),
            'url': patch_qs(self.url, extra_qs),
        }

        if self.webview_height_ratio is not None:
            out['webview_height_ratio'] = self.webview_height_ratio.value

        if self.messenger_extensions is not None:
            out['messenger_extensions'] = self.messenger_extensions

        if self.fallback_url is not None:
            out['fallback_url'] = patch_qs(self.fallback_url, extra_qs)

        if self.hide_share or self.sign_webview:
            out['webview_share_button'] = 'hide'

        return out

    def is_sharable(self):
        return not self.sign_webview


class FbPostbackButton(FbBaseButton):
    """
    That's a Facebook Postback button. When the user clicks on it, the FSM
    receives a Postback layer with the specified payload.
    """

    def __init__(self, title: TransText, payload: Any):
        super(FbPostbackButton, self).__init__(title)
        self.payload = payload

    def serialize(self, request: 'Request'):
        return {
            'type': 'postback',
            'title': render(self.title, request),
            'payload': ujson.dumps(self.payload),
        }

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.payload == other.payload)

    def __repr__(self):
        return 'Postback({}, {})'.format(repr(self.title), repr(self.payload))


class FbCallButton(FbBaseButton):
    """
    A button to trigger a phone call. The phone number must be in the format
    "+123456789"
    """

    def __init__(self, title: TransText, phone_number: Text):
        super(FbCallButton, self).__init__(title)
        self.phone_number = phone_number

    def serialize(self, request: 'Request'):
        return {
            'type': 'phone_number',
            'title': render(self.title, request),
            'payload': self.phone_number,
        }

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.phone_number == other.phone_number)

    def __repr__(self):
        return 'Postback({}, {})'\
            .format(repr(self.title), repr(self.phone_number))


class FbCardAction(FbUrlButton):
    """
    That is a simili-button that behaves like a URL button when the user clicks
    on a card.
    """

    def __init__(self,
                 url: Text,
                 sign_webview: bool=False,
                 webview_height_ratio: Optional[FbWebviewRatio]=None,
                 messenger_extensions: Optional[bool]=None,
                 fallback_url: Optional[Text]=None,
                 hide_share: Optional[bool]=None):
        super(FbCardAction, self).__init__(
            '', url, sign_webview, webview_height_ratio, messenger_extensions,
            fallback_url, hide_share
        )

    def __repr__(self):
        return 'CardAction({})'.format(repr(self.url))

    def serialize(self, request: 'Request'):
        out = super(FbCardAction, self).serialize(request)
        del out['title']
        return out


class FbCard(object):
    """
    A Facebook Card for the Generic Template.
    """
    def __init__(self,
                 title: TransText,
                 subtitle: Optional[TransText]=None,
                 buttons: Optional[List[FbBaseButton]]=None,
                 image: Optional[BaseMedia]=None,
                 default_action: Optional[FbCardAction]=None):
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

    def serialize(self, request: 'Request'):
        out = {
            'title': render(self.title, request)
        }

        if self.subtitle:
            out['subtitle'] = render(self.subtitle, request)

        if self.image:
            assert isinstance(self.image, UrlMedia)
            out['image_url'] = self.image.url

        if self.buttons:
            out['buttons'] = [b.serialize(request) for b in self.buttons]

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
