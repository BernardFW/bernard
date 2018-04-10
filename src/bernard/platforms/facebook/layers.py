from enum import (
    Enum,
)
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Optional,
    Text,
)

from bernard.i18n import (
    TransText,
    render,
)
from bernard.i18n.intents import (
    Intent,
)
from bernard.layers import (
    BaseLayer,
)

from .helpers import (
    BaseButton,
    Card,
)

if TYPE_CHECKING:
    from bernard.engine.request import Request
    from bernard.engine.platform import Platform


class MessageTag(Enum):
    """
    See https://developers.facebook.com/docs/messenger-platform
        /send-messages/message-tags
    """

    PAIRING_UPDATE = 'PAIRING_UPDATE'
    APPLICATION_UPDATE = 'APPLICATION_UPDATE'
    ACCOUNT_UPDATE = 'ACCOUNT_UPDATE'
    PAYMENT_UPDATE = 'PAYMENT_UPDATE'
    PERSONAL_FINANCE_UPDATE = 'PERSONAL_FINANCE_UPDATE'
    SHIPPING_UPDATE = 'SHIPPING_UPDATE'
    RESERVATION_UPDATE = 'RESERVATION_UPDATE'
    ISSUE_RESOLUTION = 'ISSUE_RESOLUTION'
    APPOINTMENT_UPDATE = 'APPOINTMENT_UPDATE'
    GAME_EVENT = 'GAME_EVENT'
    TRANSPORTATION_UPDATE = 'TRANSPORTATION_UPDATE'
    FEATURE_FUNCTIONALITY_UPDATE = 'FEATURE_FUNCTIONALITY_UPDATE'
    TICKET_UPDATE = 'TICKET_UPDATE'


class MessagingType(BaseLayer):
    """
    Allows to flag a message to indicate its "motive".

    See https://developers.facebook.com/docs/messenger-platform
        /send-messages#messaging_types
    """

    def __init__(self,
                 response: Optional[bool] = None,
                 update: Optional[bool] = None,
                 tag: Optional[MessageTag] = None,
                 subscription: Optional[bool] = None) -> None:
        self.response = response
        self.update = update
        self.tag = tag
        self.subscription = subscription

        self._args = [
            response,
            update,
            tag,
            subscription,
        ]

        if self._args.count(None) != 3:
            raise ValueError('You need to specify exactly one argument when '
                             'creating a MessagingType() layer.')

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.response == other.response \
               and self.update == other.update \
               and self.subscription == other.subscription

    def _repr_arguments(self):
        if self.response is not None:
            return ['response']

        if self.update is not None:
            return ['update']

        if self.tag is not None:
            return [f'tag={self.tag.value}']

        if self.subscription is not None:
            return ['subscription']

    def serialize(self):
        """
        Generates the messaging-type-related part of the message dictionary.
        """

        if self.response is not None:
            return {'messaging_type': 'RESPONSE'}

        if self.update is not None:
            return {'messaging_type': 'UPDATE'}

        if self.tag is not None:
            return {
                'messaging_type': 'MESSAGE_TAG',
                'tag': self.tag.value,
            }

        if self.subscription is not None:
            return {'messaging_type': 'NON_PROMOTIONAL_SUBSCRIPTION'}


class QuickRepliesList(BaseLayer):
    """
    This layer is a bunch of quick replies options that will be presented to
    the user.
    """

    class BaseOption(object):
        """
        Base object for a quick reply option
        """
        type = None

    class TextOption(BaseOption):
        """
        A quick reply that will trigger a text response (with a QuickReply
        layer).
        """
        type = 'text'

        def __init__(self,
                     slug: Text,
                     text: TransText,
                     intent: Optional[Intent]=None):
            self.slug = slug
            self.text = text
            self.intent = intent

        def __eq__(self, other):
            return (self.__class__ == other.__class__ and
                    self.slug == other.slug and
                    self.text == other.text and
                    self.intent == other.intent)

        def __repr__(self):
            return 'Text({}, {}, {})'.format(
                repr(self.slug),
                repr(self.text),
                repr(self.intent)
            )

    class LocationOption(BaseOption):
        """
        A quick reply that will generate a location response (with a Location
        layer).
        """
        type = 'location'

        def __init__(self):
            pass

        def __eq__(self, other):
            return self.__class__ == other.__class__

        def __repr__(self):
            return 'Location()'

    def __init__(self, options: List[BaseOption]):
        self.options = options

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        if len(self.options) != len(other.options):
            return False

        for o1, o2 in zip(self.options, other.options):
            if o1 != o2:
                return False

        return True

    def _repr_arguments(self):
        return self.options

    async def patch_register(self, register: Dict, request: 'Request'):
        """
        Store all options in the "choices" sub-register. We store both the
        text and the potential intent, in order to match both regular
        quick reply clicks but also the user typing stuff on his keyboard that
        matches more or less the content of quick replies.
        """

        register['choices'] = {
            o.slug: {
                'intent': o.intent.key if o.intent else None,
                'text': await render(o.text, request),
            } for o in self.options
            if isinstance(o, QuickRepliesList.TextOption)
        }

        return register


class QuickReply(BaseLayer):
    """
    This is what we receive when the user clicks a quick reply.
    """

    def __init__(self, slug):
        self.slug = slug

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.slug == other.slug)

    def _repr_arguments(self):
        return [self.slug]


class ButtonTemplate(BaseLayer):
    """
    Represents the Facebook "button template"
    """
    def __init__(self,
                 text: TransText,
                 buttons: List[BaseButton],
                 sharable: bool=False):
        self.text = text
        self.buttons = buttons
        self.sharable = sharable

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.text == other.text and
                self.buttons == other.buttons)

    def _repr_arguments(self):
        return [self.text, self.buttons]

    def is_sharable(self):
        """
        Is sharable if marked as and if buttons are sharable (they might
        hold sensitive data).
        """
        return self.sharable and all(x.is_sharable() for x in self.buttons)


class GenericTemplate(BaseLayer):
    """
    Represents the Facebook "generic template"
    """

    class AspectRatio(Enum):
        """
        Aspect ratio of card images
        """
        horizontal = 'horizontal'
        square = 'square'

    def __init__(self,
                 elements: List[Card],
                 aspect_ratio: Optional[AspectRatio]=None,
                 sharable: Optional[bool]=None):
        self.elements = elements
        self.aspect_ratio = aspect_ratio
        self.sharable = sharable

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                list(self.elements) == list(other.elements) and
                self.sharable == other.sharable)

    def _repr_arguments(self):
        return self.elements

    def is_sharable(self):
        """
        Can only be sharable if marked as such and no child element is blocking
        sharing due to security reasons.
        """
        return bool(
            self.sharable and
            all(x.is_sharable() for x in self.elements)
        )

    async def convert_media(self, platform: 'Platform'):
        """
        Forward the "convert media" call to all children.
        """
        for element in self.elements:
            await element.convert_media(platform)

    async def serialize(self, request: 'Request'):

        payload = {
            'template_type': 'generic',
            'elements': [await e.serialize(request) for e in self.elements],
            'sharable': self.is_sharable(),
        }

        if self.aspect_ratio:
            payload['image_aspect_ratio'] = self.aspect_ratio.value

        return payload


class OptIn(BaseLayer):
    """
    That kind of layers indicates that the bot now has a right to talk to the
    specified user, even if the user did not start a conversation right now.
    """

    def __init__(self, ref=''):
        self.ref = ref

    def __eq__(self, other):
        return (self.__class__ == other.__class__
                and self.ref == other.ref)

    def _repr_arguments(self):
        return [self.ref]
