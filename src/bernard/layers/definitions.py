# coding: utf-8
from typing import Dict, Text as TextT, List, Optional, TYPE_CHECKING, \
    TypeVar, Type
from bernard.i18n import TransText, render

if TYPE_CHECKING:
    from bernard.engine.request import Request


L = TypeVar('L')


class BaseLayer(object):
    def patch_register(self, register: Dict, request: 'Request') -> Dict:
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

    def become(self, layer_type: Type[L], request: 'Request') -> L:
        """
        Transform this layer into another layer type
        """

        raise ValueError('Cannot become "{}"'.format(layer_type.__name__))


class Text(BaseLayer):
    """
    The text layer simply represents a text message.
    """

    def __init__(self, text: TransText):
        self.text = text

    def can_become(self):
        return [RawText]

    def become(self, layer_type: Type[L], request: 'Request'):
        if layer_type != RawText:
            super(Text, self).become(layer_type, request)

        return RawText(render(self.text, request))


class RawText(BaseLayer):
    """
    That is a text message that warranties it will never have to be translated.
    """

    def __init__(self, text: TextT):
        self.text = text


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
                     intents_key: Optional[TextT]=None):
            self.slug = slug
            self.text = text
            self.intents_key = intents_key

    class LocationOption(BaseOption):
        """
        A quick reply that will generate a location response (with a Location
        layer).
        """
        type = 'location'

        def __init__(self):
            pass

    def __init__(self, options: List[BaseOption]):
        self.options = options

    def patch_register(self, register: Dict, request: 'Request'):
        """
        Store all options in the "choices" sub-register. We store both the
        text and the potential intent, in order to match both regular
        quick reply clicks but also the user typing stuff on his keyboard that
        matches more or less the content of quick replies.
        """

        # noinspection PyUnresolvedReferences
        register['choices'] = {
            o.slug: {
                'intent': o.intents_key,
                'text': render(o.text, request),
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
