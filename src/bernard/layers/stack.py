# coding: utf-8
from typing import List, TypeVar, Text, Dict, TYPE_CHECKING, Type

from bernard.utils import RoList, ClassExp
from .definitions import BaseLayer

if TYPE_CHECKING:
    from bernard.engine.request import Request
    from bernard.engine.platform import Platform


L = TypeVar('L')


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
        self._transformed = {}
        self.layers = layers
        self.annotation = None

    def __eq__(self, other):
        # noinspection PyProtectedMember
        return (self.__class__ == other.__class__ and
                self._layers == other._layers)

    def __repr__(self):
        return 'Layer({})'.format(', '.join(repr(x) for x in self._layers))

    @property
    def layers(self) -> List['BaseLayer']:
        """
        Return a read-only version of the layers list, so people don't get
        tempted to append stuff to the list (which would break the index).
        """
        # noinspection PyTypeChecker
        return RoList(self._layers, True)

    @layers.setter
    def layers(self, value: List['BaseLayer']):
        """
        Perform a copy of the layers list in order to avoid the list changing
        without updating the index.

        Then update the index.
        """
        self._layers = list(value)  # type: List[BaseLayer]
        self._index = self._make_index()
        self._transformed = {}

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

    async def transform(self, request):
        out = {}

        for layer in self._layers:  # type: BaseLayer
            for become in layer.can_become():
                b_layer = await layer.become(become, request)
                out[become] = out.get(become, []) + [b_layer]

        self._transformed = out

    def has_layer(self, class_: Type[L], became: bool=True) -> bool:
        """
        Test the presence of a given layer type.

        :param class_: Layer class you're interested in.
        :param became: Allow transformed layers in results
        """

        return (class_ in self._index or
                (became and class_ in self._transformed))

    def get_layer(self, class_: Type[L], became: bool=True) -> L:
        """
        Return the first layer of a given class. If that layer is not present,
        then raise a KeyError.

        :param class_: class of the expected layer
        :param became: Allow transformed layers in results
        """

        try:
            return self._index[class_][0]
        except KeyError:
            if became:
                return self._transformed[class_][0]
            else:
                raise

    def get_layers(self, class_: Type[L], became: bool=True) -> List[L]:
        """
        Returns the list of layers of a given class. If no layers are present
        then the list will be empty.

        :param class_: class of the expected layers
        :param became: Allow transformed layers in results
        """

        out = self._index.get(class_, [])

        if became:
            out += self._transformed.get(class_, [])

        return out

    def describe(self) -> Text:
        return ', '.join(
            s.__class__.__name__ for s in self._layers
        )

    async def patch_register(self, register: Dict, request: 'Request'):
        for layer in self._layers:  # type: BaseLayer
            register = await layer.patch_register(register, request)
        return register

    def match_exp(self, expression: Text):
        e = ClassExp(expression)
        return e.match(self._layers)

    async def convert_media(self, platform: 'Platform') -> None:
        """
        Polls all the layers to convert the media inside.
        """

        for layer in self.layers:
            await layer.convert_media(platform)


def stack(*layers: BaseLayer):
    return Stack(list(layers))
