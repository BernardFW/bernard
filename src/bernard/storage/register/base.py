# coding: utf-8
from typing import Text, Any, Dict, Iterator, Union, Optional
from collections import Mapping, Sequence


# noinspection PyTypeChecker
def make_ro(obj: Union[str, bytes, int, float, bool, None, Mapping, Sequence]):
    """
    Make a json-serializable type recursively read-only

    :param obj: Any json-serializable type 
    """

    if isinstance(obj, (str, bytes, int, float, bool, RoDict, RoList)) \
            or obj is None:
        return obj
    elif isinstance(obj, Mapping):
        return RoDict(obj)
    elif isinstance(obj, Sequence):
        return RoList(obj)
    else:
        raise ValueError('Trying to make read-only an object of type "{}"'
                         .format(obj.__class__.__name__))


class RoDict(Mapping):
    """
    Wrapper around a dict to make it read-only.
    """

    def __init__(self, data: Dict[Text, Any]):
        self._data = data

    def __getitem__(self, key: Text) -> Any:
        """
        Gets the item from data while making it read-only first
        """

        return make_ro(self._data[key])

    def __len__(self) -> int:
        """
        Proxy to data's length
        """

        return len(self._data)

    def __iter__(self) -> Iterator[Any]:
        """
        Proxy to data's iterator
        """

        return iter(self._data)


class RoList(Sequence):
    """
    Wrapper around a list to make it read-only
    """

    def __init__(self, data: Sequence):
        """
        Store data we're wrapping
        """
        self._data = data

    def __getitem__(self, index: int) -> Any:
        """
        Proxy to data's get item
        """
        return make_ro(self._data[index])

    def __len__(self):
        """
        Proxy to data's length
        """
        return len(self._data)


class Register(RoDict):
    """
    Once the new register is built, save it using `replace()`. It will later
    be inserted into the store.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a "replacement" member, that external classes can read to see
        if there is some replacement data ready.
        """
        super(Register, self).__init__(*args, **kwargs)
        self.replacement = None  # type: Optional[Dict[Text, Any]]


class BaseRegisterStore(object):
    """
    Interface for register storage.

    The register is atomic: you read it all at once, lock out other readers
    and then save it all at once.

    You can use it like this:

    >>> async def do_something_with_register():
    >>>     store = BaseRegisterStore()
    >>>     async with store.work_on_register('your-conversation-id') as reg:
    >>>         # You can access read-only data
    >>>         assert reg['some_key']
    >>>         # Then you build up what you want to store back
    >>>         out = {'some_stuff': True}
    >>>         # And finally, you store it back
    >>>         reg.replacement = out

    This class implements the context manager logic but 4 methods have to be
    implemented to communicate with an actual storage backend.
    """

    def work_on_register(self, key: Text) -> "RegisterContextManager":
        """
        Create the context manager
        """
        return RegisterContextManager(key, self)

    async def _start(self, key: Text) -> None:
        """
        That's when you start working on a key. You should start locking here.
        """
        raise NotImplementedError

    async def _get(self, key: Text) -> Any:
        """
        There you fetch the data of the register.
        """
        raise NotImplementedError

    async def _replace(self, key: Text, data: Dict[Text, Any]) -> None:
        """
        This function will be called if there is a replacement in order to
        store it into the register. This will be called only once by the
        context manager, even if the replacement was set several times (only
        the last value counts).
        """
        raise NotImplementedError

    async def _finish(self, key: Text) -> None:
        """
        This is called when everything is done. You should release the lock
        here. This will get called even if the replace failed.
        """
        raise NotImplementedError


# noinspection PyProtectedMember
class RegisterContextManager(object):
    """
    Handles the context of the register: call the right methods of the storage
    at the right time and provide the register.
    """

    def __init__(self, key: Text, store: BaseRegisterStore):
        self.key = key
        self.register = None
        self.store = store

    async def __aenter__(self):
        """
        Start the lock and fetch data from the store in order to provide it.
        """

        await self.store._start(self.key)
        data = await self.store._get(self.key)
        self.register = Register(data)
        return self.register

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Whatever happened, if there is a replacement we'll store it. And even
        if that fails, the lock is lifted afterwards.
        """

        try:
            if self.register.replacement is not None:
                await self.store._replace(self.key, self.register.replacement)
        finally:
            await self.store._finish(self.key)
