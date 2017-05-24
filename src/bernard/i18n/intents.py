# config: utf-8
from typing import List, Text, Optional, TYPE_CHECKING
from bernard.conf import settings
from bernard.utils import import_class, run
from .loaders import BaseIntentsLoader, IntentDict

if TYPE_CHECKING:
    from bernard.engine.request import Request


class IntentsDb(object):
    """
    Database of intents. In the future it will handle different langs but right
    now it only handles one.
    """

    def __init__(self):
        self.dict = {}  # type: IntentDict
        self.loaders = []  # type: List[BaseIntentsLoader]
        self._init_loaders()

    def _init_loaders(self) -> None:
        """
        Gets loaders from conf, make instances and subscribe to them.
        """

        for loader in settings.I18N_INTENTS_LOADERS:
            loader_class = import_class(loader['loader'])
            instance = loader_class()
            instance.on_update(self.update)
            run(instance.load(**loader['params']))

    def update(self, new_data: IntentDict):
        """
        Receive an update from the loaders.
        """

        self.dict.update(new_data)

    def get(self, key: Text):
        """
        Get a single set of intents.
        """

        return self.dict[key]


class Intent(object):
    """
    Represents an intent to be resolved later.
    """

    def __init__(self, db: Optional[IntentsDb], key: Text):
        self.db = db
        self.key = key

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.key == other.key)

    def __repr__(self):
        return 'Intent({})'.format(repr(self.key))

    # noinspection PyUnusedLocal
    def strings(self, request: Optional['Request']=None):
        """
        For the given request, find the list of strings of that intent. If the
        intent does not exist, it will raise a KeyError.
        """

        return self.db.get(self.key)


class IntentsMaker(object):
    """
    Utility class to be used as singleton and produce Intents objects easily
    from anywhere in the code.
    """

    def __init__(self, db: IntentsDb=None):
        self.db = db

        if not self.db:
            self._refresh_intents_db()

    def _refresh_intents_db(self):
        """
        Re-read the config and re-generate the intents DB.
        """

        self.db = IntentsDb()

    def __getattr__(self, key: Text) -> Intent:
        """
        Generate an intent. Use it this way:

        >>> i = IntentsMaker()
        >>> print(i.FOO.strings())
        """

        return Intent(self.db, key)
