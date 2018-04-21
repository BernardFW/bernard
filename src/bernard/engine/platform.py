# coding: utf-8
import asyncio
from typing import (
    Any,
    Callable,
    Coroutine,
    List,
    Optional,
    Text,
)

import aiohttp
from aiohttp.web_urldispatcher import (
    UrlDispatcher,
)

from bernard.engine.request import (
    Request,
)
from bernard.engine.responder import (
    Responder,
    UnacceptableStack,
)
from bernard.layers import (
    Stack,
)
from bernard.media.base import (
    BaseMedia,
)
from bernard.utils import (
    import_class,
)

from .request import (
    BaseMessage,
)

MessageCallback = Callable[[BaseMessage, Responder, bool], None]


class Platform(object):
    """
    Base class for the platforms. You need to overload it in order to create
    your own platform.

    To create a new platform, you need two things:

        - Call `_notify()` when you receive a message from the platform
        - Implement `accept()`

    The `fsm_creates_task` attribute indicates one of two work modes:

        - True: the callbacks are in charge of starting their own tasks
        - False: the callbacks will be awaited. Also, the return value of the
          last callback will be stored in `_register`. This mode is created
          for unit tests.
    """

    NAME = None

    fsm_creates_task = True

    def __init__(self):
        self._listeners = []  # type: List[MessageCallback]
        self._register = None
        self._id = None

    async def async_init(self):
        pass

    @classmethod
    def settings(cls):
        """
        Find the settings for the current class inside the platforms
        configuration.
        """

        from bernard.platforms.management import get_platform_settings

        for platform in get_platform_settings():
            candidate = import_class(platform['class'])
            if candidate == cls:
                return platform.get('settings', {})

    @property
    def id(self):
        """
        Allows to get several instances of the same class, using a custom
        `name` attribute in the platform configuration.
        """

        if self._id:
            return self._id

        return self.NAME

    def on_message(self, cb: MessageCallback):
        """
        Register a callback to listen for incoming messages.
        """

        self._listeners.append(cb)

    async def _notify(self, message: BaseMessage, responder: Responder):
        """
        Notify all callbacks that a message was received.
        """
        for cb in self._listeners:
            coro = cb(message, responder, self.fsm_creates_task)

            if not self.fsm_creates_task:
                self._register = await coro

    def accept(self, stack: Stack):
        """
        Return True if the platform can accept the stack provided as argument,
        and False otherwise.
        """
        raise NotImplementedError

    async def send(self, request: Request, stack: Stack) -> None:
        """
        Send a stack to the user
        """
        raise NotImplementedError

    async def ensure_usable_media(self, media: BaseMedia) -> BaseMedia:
        """
        Ensure that the media passed as argument can be used to send on the
        platform.

        If the media is already usable, it is returned as-is.
        """
        raise NotImplementedError

    @classmethod
    async def self_check(cls):
        """
        Run the self health-check. This one is a dummy one.
        """

        for i in []:
            yield

    def hook_up(self, router: UrlDispatcher):
        """
        This is where the platform can register its routes (for the hooks and
        so on).
        """

        pass

    async def message_from_token(self, token: Text, payload: Any) \
            -> Optional[BaseMessage]:
        """
        Given a token and a payload, create a message for this platform with
        a Postback layer holding the payload.
        """

        raise NotImplementedError

    async def inject_message(self, message: BaseMessage) -> None:
        """
        Injects a message into the platform and handles it in the FSM
        """

        raise NotImplementedError


class SimplePlatform(Platform):
    PATTERNS = {}

    def __init__(self):
        super(SimplePlatform, self).__init__()
        self.session = None

    async def async_init(self):
        """
        During async init we just need to create a HTTP session so we can keep
        outgoing connexions to the platform alive.
        """
        self.session = aiohttp.ClientSession()
        asyncio.get_event_loop().create_task(self._deferred_init())

    async def _deferred_init(self):
        """
        Run those things in a sepearate tasks as they are not required for the
        bot to work and they take a lot of time to run.
        """
        raise NotImplementedError

    def accept(self, stack: Stack):
        """
        Checks that the stack can be accepted according to the `PATTERNS`.

        If the pattern is found, then its name is stored in the `annotation`
        attribute of the stack.
        """

        for name, pattern in self.PATTERNS.items():
            if stack.match_exp(pattern):
                stack.annotation = name
                return True
        return False

    def send(self, request: Request, stack: Stack) -> Coroutine:
        """
        Send a stack to the platform.

        Actually this will delegate to one of the `_send_*` functions depending
        on what the stack looks like.
        """

        if stack.annotation not in self.PATTERNS:
            if not self.accept(stack):
                raise UnacceptableStack('Cannot accept stack {}'.format(stack))

        func = getattr(self, '_send_' + stack.annotation)
        return func(request, stack)

    def ensure_usable_media(self, media: BaseMedia) -> BaseMedia:
        raise NotImplementedError

    async def message_from_token(self, token: Text, payload: Any)\
            -> Optional[BaseMessage]:
        raise NotImplementedError

    async def inject_message(self, message: BaseMessage) -> None:
        raise NotImplementedError


class PlatformError(Exception):
    """
    Base platform error
    """


class PlatformDoesNotExist(PlatformError):
    """
    Happens when a non-existing platform is asked for initialization
    """


class PlatformOperationError(PlatformError):
    """
    An operation on the platform failed
    """
