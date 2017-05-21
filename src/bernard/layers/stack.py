# coding: utf-8
from typing import List, TypeVar
from bernard.utils import RoList
from .definitions import BaseLayer


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

    def has_layer(self, class_: L) -> bool:
        """
        Test the presence of a given layer type.

        :param class_: Layer class you're interested in.
        """

        return class_ in self._index

    def get_layer(self, class_: L) -> L:
        """
        Return the first layer of a given class. If that layer is not present,
        then raise a KeyError.

        :param class_: class of the expected layer 
        """

        return self._index[class_][0]

    def get_layers(self, class_: L) -> List[L]:
        """
        Returns the list of layers of a given class. If no layers are present
        then the list will be empty.

        :param class_: class of the expected layers
        """
        return self._index.get(class_, [])
