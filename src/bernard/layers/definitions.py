# coding: utf-8
from typing import (
    TYPE_CHECKING,
    Dict,
    NamedTuple,
    Optional,
    Text as TextT,
    Type,
    TypeVar,
)

from bernard.i18n import (
    TransText,
    render,
)

if TYPE_CHECKING:
    from bernard.engine.request import Request
    from bernard.engine.platform import Platform
    from bernard.engine.request import BaseMessage


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


class MultiText(Text):
    """
    That's exactly like a Text layer but which can output several messages at
    once.
    """


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


class Markdown(BaseLayer):
    """
    Like the Text but for Markdown.
    """

    def __init__(self, text: TextT):
        self.text = text

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.text == other.text

    def _repr_arguments(self):
        if len(self.text) > 15:
            text = self.text[:12] + '...'
        else:
            text = self.text

        return [text]


class Sleep(BaseLayer):
    """
    Permit to slow down the debit of the message
    """

    def __init__(self, duration: float):
        self.duration = duration

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.duration == other.duration)

    def _repr_arguments(self):
        return [self.duration]


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


class Message(BaseLayer):
    """
    This layer represents a message embedded in another
    """

    def __init__(self, message: 'BaseMessage'):
        from bernard.layers import Stack
        self.message = message
        self.stack: Stack = Stack(message.get_layers())

    def _repr_arguments(self):
        return [x for x in self.stack.layers]

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.stack == other.stack


class Typing(BaseLayer):
    """
    Indicates that the bot is currently "typing" its response
    """

    def __init__(self, active=True):
        self.active = active

    def _repr_arguments(self):
        return [self.active]

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
            and self.active == other.active
