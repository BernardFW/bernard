# coding: utf-8
from functools import wraps
from typing import Text, Dict, Any, Iterator
from bernard.conf import settings
from bernard.core.health_check import HealthCheckFail
from bernard.engine.state import BaseState
from bernard.utils import import_class


Context = Dict[Text, Any]


def create_context_store(name='default',
                         ttl=settings.CONTEXT_DEFAULT_TTL,
                         store=settings.CONTEXT_STORE) -> 'BaseContextStore':
    """
    Create a context store. By default using the default configured context
    store, but you can use a custom class if you want to using the `store`
    setting.

    The time to live of each store (aka there is one per conversation) is
    defined by the `ttl` value, which is also inferred by default from the
    configuration.

    You can have several stores existing in parallel. To make the distinction
    between them you need to give them different names, using the `name`
    parameter.

    The usage looks like:

    >>> cs = create_context_store()
    >>> class Hello(BaseTestState):
    >>>     @cs.inject(['foo'])
    >>>     async def handle(self, context):
    >>>         logger.debug('foo is %s', context['foo'])
    >>>
    >>>     async def missing_context(self):
    >>>         self.send(lyr.Text('`foo` is not in context'))

    This requires that `foo` is present in the context in order to enter the
    handler.

    See `BaseContextStore.inject()` for more info.
    """

    store_class = import_class(store['class'])
    return store_class(name=name, ttl=ttl, **store['params'])


class BaseContextStore(object):
    """
    Defines the interface of a context store.

    The context store stores a dictionary object in whichever way it wants (by
    example in a Redis database). Each context is a plain dictionary object.
    Each context is created for one conversation and expires after X seconds.

    The implementer of context store must implement a `_get()` and a `_set()`
    method.

    For a user of this class, the main entry point is `inject()`.
    """

    def __init__(self, name, ttl, **kwargs):
        # noinspection PyArgumentList
        super(BaseContextStore, self).__init__(**kwargs)

        self.name = name
        self.ttl = ttl
        self._init_done = False

    async def async_init(self) -> None:
        pass

    async def ensure_async_init(self) -> None:
        """
        This allows to lazily do the async init
        """

        if not self._init_done:
            await self.async_init()
            self._init_done = True

    async def _get(self, key: Text) -> Context:
        """
        Implement this as a method to get the context for the given key.
        """
        raise NotImplementedError

    async def _set(self, key: Text, data: Context) -> None:
        """
        Implement this as a method to set the context at the given key.
        """
        raise NotImplementedError

    def open(self, key: Text) -> 'ContextContextManager':
        """
        Opens a context using the a Python context manager.

        The `key` is the arbitrary key identifying the context.
        """
        return ContextContextManager(key, self)

    def inject(self,
               require=None,
               fail='missing_context',
               var_name='context'):
        """
        This is a decorator intended to be used on states (and actually only
        work on state handlers).

        The `require` argument is a list of keys to be checked in the context.
        If at least one of them is missing, then instead of calling the handler
        another method will be called. By default the method is
        `missing_context` but it can be configured using the `fail` argument.

        The context will be injected into the handler as a keyword arg. By
        default, the arg is expected to be named `context` but you can change
        it to anything you'd like using `var_name`.

        See `create_context_store()` for a full example.
        """

        def decorator(func):
            async def health_check(cls) -> Iterator[HealthCheckFail]:
                if not callable(getattr(cls, fail, None)):
                    yield HealthCheckFail(
                        '00001',
                        f'State "{cls.__name__}" has no method "{fail}" to '
                        f'fall back to if required attributes are missing '
                        f'from the context.'
                    )

            if require:
                func.health_check = health_check

            @wraps(func)
            async def wrapper(state: BaseState, **kwargs):
                conv_id = state.request.conversation.id
                key = f'context::{self.name}::{conv_id}'

                x = self.open(key)
                async with x as context:
                    for item in (require or []):
                        if item not in context:
                            return await getattr(state, fail)(state, **kwargs)

                    kwargs[var_name] = context
                    return await func(state, **kwargs)

            return wrapper
        return decorator


# noinspection PyProtectedMember
class ContextContextManager(object):
    """
    A (Python) context manager to handle the opening and saving/closing of the
    (Bernard) context.
    """

    def __init__(self, key: Text, store: BaseContextStore):
        self.key = key
        self.data = None
        self.store = store

    async def __aenter__(self):
        """
        When we enter the (Python) context, we load the (Bernard) context into
        a plain dictionary and return it.
        """

        await self.store.ensure_async_init()
        self.data = await self.store._get(self.key)
        return self.data

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        When leaving the (Python) context, the (Bernard) context is sent back
        to the storage for saving.
        """

        await self.store._set(self.key, self.data)
