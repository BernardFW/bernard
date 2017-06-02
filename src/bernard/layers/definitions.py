# coding: utf-8
from enum import Enum
from typing import Dict, Text as TextT, List, Optional, TYPE_CHECKING, \
    TypeVar, Type, NamedTuple
from bernard.i18n import TransText, render
from bernard.i18n.intents import Intent
from .helpers import FbBaseButton, FbCard

if TYPE_CHECKING:
    from bernard.engine.request import Request
    from bernard.engine.platform import Platform


L = TypeVar('L')


class BaseLayer(object):
    def __eq__(self, other):
        raise NotImplementedError

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ','.join(repr(x) for x in self._repr_arguments()),
        )

    def _repr_arguments(self):
        raise NotImplementedError

    async def patch_register(self, register: Dict, request: 'Request') -> Dict:
        """
        If you want to put a value in the transition register, you can overload
        this function and patch the provided register.

        Keys match different operations. By example, for quick replies:

        >>> {
        >>>     'choices': {
        >>>         'yes': {
        >>>             'intents': 'YES',
        >>>         },
        >>>         'no': {
        >>>             'intents': 'NO',
        >>>         }
        >>>     }
        >>> }

        It's up to the layers implementations to set up consistent conventions
        for this register.

        This function will be called in the order of layers. The implementation
        can choose to add information to what previous layers inserted or to
        overwrite it completely. That is why the previous output is provided
        as argument.
        """

        return register

    def can_become(self):
        """
        This indicates other layer classes that you can transform this layer
        into from a request.
        """
        return []

    async def become(self, layer_type: Type[L], request: 'Request') -> L:
        """
        Transform this layer into another layer type
        """

        raise ValueError('Cannot become "{}"'.format(layer_type.__name__))

    async def convert_media(self, platform: 'Platform') -> None:
        """
        Convert this layer's media if needed
        """
        pass


class Text(BaseLayer):
    """
    The text layer simply represents a text message.
    """

    def __init__(self, text: TransText):
        self.text = text

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.text == other.text)

    def _repr_arguments(self):
        return [self.text]

    def can_become(self):
        """
        A Text can become a RawText
        """
        return [RawText]

    async def become(self, layer_type: Type[L], request: 'Request'):
        """
        Transforms the translatable string into an actual string and put it
        inside a RawText.
        """
        if layer_type != RawText:
            super(Text, self).become(layer_type, request)

        return RawText(await render(self.text, request))


class RawText(BaseLayer):
    """
    That is a text message that warranties it will never have to be translated.
    """

    def __init__(self, text: TextT):
        self.text = text

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.text == other.text)

    def _repr_arguments(self):
        return [self.text]


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
                     slug: TextT,
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

        # noinspection PyUnresolvedReferences
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


class Postback(BaseLayer):
    """
    That's some arbitrary data sent by the platform when the user clicks a
    button. Usually, it's buttons that were previously programmed by the bot.
    """

    def __init__(self, payload):
        self.payload = payload

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.payload == other.payload)

    def _repr_arguments(self):
        return [self.payload]


class BaseMediaLayer(BaseLayer):
    """
    Base for all layer types holding a media. All media layers have the same
    code, but the subclasses exist to make it easier to filter out messages
    based on what kind of media they have.
    """

    def __init__(self, media):
        self.media = media

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.media == other.media)

    def _repr_arguments(self):
        return [self.media]


class Image(BaseMediaLayer):
    """
    Represents an image
    """
    pass


class Audio(BaseMediaLayer):
    """
    Represents some audio
    """
    pass


class File(BaseMediaLayer):
    """
    Represents an arbitrary file
    """
    pass


class Video(BaseMediaLayer):
    """
    Represents a video
    """
    pass


class Location(BaseLayer):
    """
    That's when the user sends his location
    """

    class Point(NamedTuple):
        """
        Representation as tuple of a user location
        """

        lon: float
        lat: float

    def __init__(self, point: Point):
        self.point = point

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.point == other.point)

    def _repr_arguments(self):
        return [self.point]


class FbButtonTemplate(BaseLayer):
    """
    Represents the Facebook "button template"
    """
    def __init__(self,
                 text: Text,
                 buttons: List[FbBaseButton],
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


class FbGenericTemplate(BaseLayer):
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
                 elements: List[FbCard],
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


class LinkClick(BaseLayer):
    """
    That layer is triggered when the user clicks on a link
    """

    def __init__(self, url: Text, slug: Optional[Text]=None):
        self.url = url
        self.slug = slug

    def _repr_arguments(self):
        if self.slug:
            return [self.slug]
        else:
            return [self.url]

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.slug == other.slug and
                self.url == other.url)


class CloseWebview(BaseLayer):
    """
    Triggered when a webview gets closed.
    """

    def __init__(self, slug: Optional[Text]):
        self.slug = slug

    def _repr_arguments(self):
        return [self.slug]

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.slug == other.slug)
