from typing import List, Type, Text, Callable, TypeVar

from bernard.conf import settings
from bernard.core.health_check import HealthCheckFail
from bernard.utils import import_class
from ._builtins import BaseMiddleware


C = TypeVar('C')


class Caller(object):
    """
    This object allows to create functions which can call each other
    recursively without knowing in advance the list of functions to call.

    It's useful to stack middlewares.
    """

    def __init__(self,
                 manager: 'MiddlewareManager',
                 name: Text,
                 final: Callable) -> None:
        """
        Save attributes and generate the proper stack of calls.

        `manager` is the middleware manager from which the stack is built
        `name` is the name of the function to call
        `final` is the final function to call, which will end the recursion
        """

        self.manager = manager
        self.name = name
        self.final = final
        self._stack = self._build_stack()
        self._pos = 0
        self._complete = False

    def _build_stack(self) -> List[Callable]:
        """
        Generates the stack of functions to call. It looks at the ordered list
        of all middlewares and only keeps those which have the method we're
        trying to call.
        """

        stack = []

        for m in self.manager.middlewares:
            try:
                stack.append(getattr(m(self), self.name))
            except AttributeError:
                pass

        return stack

    async def __call__(self, *args, **kwargs):
        """
        Calls the next function in the stack.
        """

        if self._pos == 0:
            is_root = True
        else:
            is_root = False

        if self._pos < len(self._stack):
            func = self._stack[self._pos]
            self._pos += 1
            out = await func(*args, **kwargs)
        elif self._pos == len(self._stack):
            self._pos += 1
            out = await self.final(*args, **kwargs)
            self._complete = True
        else:
            raise ValueError('A caller cannot be called twice')

        if is_root and not self._complete:
            # noinspection PyUnresolvedReferences
            faulty = self._stack[self._pos - 1].__qualname__
            raise TypeError(f'"{faulty}" did not call `self.next()`, or '
                            f'forgot to await it')

        return out


class MiddlewareManager(object):
    """
    Manages the middlewares and allows to run them.

    Typical use:

    >>> async def do_something(x):
    >>>     return x + 1
    >>>
    >>> func = MiddlewareManager.instance().get('do_something', do_something)
    >>> print(await func(0))
    """

    _instance = None

    def __init__(self):
        """
        Don't call directly, use `instance()` instead.
        """

        self._middlewares_classes: List[Text] = settings.MIDDLEWARES
        self.middlewares: List[Type[BaseMiddleware]] = []

    @classmethod
    def instance(cls) -> 'MiddlewareManager':
        """
        Creates, initializes and returns a unique MiddlewareManager instance.
        """

        if cls._instance is None:
            cls._instance = cls()
            cls._instance.init()
        return cls._instance

    @classmethod
    def health_check(cls):
        """
        Checks that the configuration makes sense.
        """

        try:
            assert isinstance(settings.MIDDLEWARES, list)
        except AssertionError:
            yield HealthCheckFail(
                '00005',
                'The "MIDDLEWARES" configuration key should be assigned '
                'to a list',
            )
            return

        for m in settings.MIDDLEWARES:
            try:
                c = import_class(m)
            except (TypeError, ValueError, AttributeError, ImportError):
                yield HealthCheckFail(
                    '00005',
                    f'Cannot import middleware "{m}"',
                )
            else:
                if not issubclass(c, BaseMiddleware):
                    yield HealthCheckFail(
                        '00005',
                        f'Middleware "{m}" does not implement '
                        f'"BaseMiddleware"',
                    )

    def init(self):
        """
        Imports and caches all middleware classes.
        """

        self.middlewares = [import_class(c) for c in self._middlewares_classes]

    def get(self, name: Text, final: C) -> C:
        """
        Get the function to call which will run all middlewares.

        :param name: Name of the function to be called
        :param final: Function to call at the bottom of the stack (that's the
                      one provided by the implementer).
        :return:
        """

        # noinspection PyTypeChecker
        return Caller(self, name, final)
