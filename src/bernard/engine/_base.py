# coding: utf-8
import asyncio
import logging
from typing import (
    AsyncIterator,
    Dict,
    Optional,
)

from bernard.conf import (
    settings,
)
from bernard.core.health_check import (
    HealthCheckFail,
)
from bernard.middleware import (
    MiddlewareManager,
)
from bernard.storage.register import (
    BaseRegisterStore,
)
from bernard.utils import (
    import_class,
)

from .app import (
    RootApp,
)
from .request import (
    BaseMessage,
    Request,
)
from .responder import (
    Responder,
)

logger = logging.getLogger('bernard.fsm')


class Engine(object):
    """
    Core engine. It creates the root app and does some initialisation, yet its
    responsibility is now quite limited. Most of the funk happens in the apps.
    """

    def __init__(self):
        self.register = self._make_register()
        self.app = RootApp()

    async def health_check(self) -> AsyncIterator[HealthCheckFail]:
        async for check in self.app.health_check():
            yield check

    async def async_init(self):
        """
        The register might need to be initialized in a loop
        """

        await self.register.async_init()

    def _make_register(self) -> BaseRegisterStore:
        """
        Make the register storage.
        """

        s = settings.REGISTER_STORE
        store_class = import_class(s['class'])
        return store_class(**s['params'])

    async def _handle_message(self,
                              message: BaseMessage,
                              responder: Responder) -> Optional[Dict]:
        """
        Handles a message: find a state and run it.

        :return: The register that was saved
        """

        async def noop(request: Request, responder: Responder):
            pass

        mm = MiddlewareManager.instance()
        reg_manager = self.register\
            .work_on_register(message.get_conversation().id)

        async with reg_manager as reg:
            request = Request(message, reg)
            await request.transform()

            if not request.stack.layers:
                return

            logger.debug('Incoming message: %s', request.stack)
            await mm.get('pre_handle', noop)(request, responder)

            return await self.app.handle_message(None, request, responder, {})

    def handle_message(self,
                       message: BaseMessage,
                       responder: Responder,
                       create_task: True):
        """
        Public method to handle a message. It requires:

            - A message from the platform
            - A responder from the platform

        If `create_task` is true, them the task will automatically be added to
        the loop. However, if it is not, the coroutine will be returned and it
        will be the responsibility of the caller to run/start the task.
        """

        coro = self._handle_message(message, responder)

        if create_task:
            loop = asyncio.get_event_loop()
            loop.create_task(coro)
        else:
            return coro
