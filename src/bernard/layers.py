# coding: utf-8
from typing import Dict, Text as TextT, List, Optional, Type
from bernard.i18n import TransText, serialize
from bernard.utils import RoList


class Stack(object):
    """
    The stack holds several layers and allows quick access to specific content.
    This is useful by example for transitions to check if they have anything
    interesting to find.

    This stack has a .layers attribute that you can read to get the list of
    layers. However, if you want to change that list, you must set it all at
    once, because there is an internal index that is being computed.

    You have helper functions to filter through layer types and so on.
    """

    def __init__(self, layers: List['BaseLayer']):
        self._layers = []
        self._index = {}
        self.layers = layers

    @property
    def layers(self) -> List['BaseLayer']:
        """
        Return a read-only version of the layers list, so people don't get
        tempted to append stuff to the list (which would break the index).
        """
        # noinspection PyTypeChecker
        return RoList(self._layers)

    @layers.setter
    def layers(self, value: List['BaseLayer']):
        """
        Perform a copy of the layers list in order to avoid the list changing
        without updating the index.

        Then update the index.
        """
        self._layers = list(value)
        self._index = self._make_index()

    def _make_index(self):
        """
        Perform the index computation. It groups layers by type into a
        dictionary, to allow quick access.
        """

        out = {}

        for layer in self._layers:
            cls = layer.__class__
            out[cls] = out.get(cls, []) + [layer]

        return out

    def has_layer(self, class_: Type['BaseLayer']) -> bool:
        """
        Test the presence of a given layer type.

        :param class_: Layer class you're interested in.
        """

        return class_ in self._index

    def get_layer(self, class_: Type['BaseLayer']) -> Optional['BaseLayer']:
        """
        Return the first layer of a given class, or None if not present.

        :param class_: class of the expected layer 
        """

        try:
            return self._index[class_][0]
        except KeyError:
            return None

    def get_layers(self, class_: Type['BaseLayer']) -> List['BaseLayer']:
        """
        Returns the list of layers of a given class. If no layers are present
        then the list will be empty.

        :param class_: class of the expected layers
        """
        return self._index.get(class_, [])


class BaseLayer(object):
    def patch_register(self, register: Dict) -> Dict:
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

        :param register: a dictionary to patch
        """

        return register


class Text(BaseLayer):
    """
    The text layer simply represents a text message.
    """

    def __init__(self, text: TransText):
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

    def patch_register(self, register: Dict):
        """
        Store all options in the "choices" sub-register. We store both the
        text and the potential intent, in order to match both regular
        quick reply clicks but also the user typing stuff on his keyboard that
        matches more or less the content of quick replies.
        """

        # noinspection PyUnresolvedReferences
        register['choices'] = {
            o.slug: {
                'intents': o.intents_key,
                'text': serialize(o.text),
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
