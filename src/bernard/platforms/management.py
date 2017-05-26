# coding: utf-8
from typing import Text
from bernard.engine.fsm import FSM
from bernard.engine.platform import PlatformDoesNotExist
from bernard.platforms.facebook.platform import Facebook


class PlatformManager(object):
    """
    That is the core of the system. This class has the responsibilities to:

        - Create the platform instances
        - Create the FSM
        - Hook the platforms to the FSM

    For unit testing purposes it can also wipe existing instances and start
    again.
    """

    def __init__(self):
        self.fsm = None
        self.platforms = {}

    @property
    def _is_init(self):
        """
        Check if initialization was done
        :return: 
        """
        return self.fsm is not None

    async def init(self):
        """
        Creates the FSM and the cache. It can be called several times to reset
        stuff (like for unit tests...).
        """
        self.fsm = FSM()
        await self.fsm.async_init()

        self.platforms = {}

    async def build_facebook(self):
        """
        Build the Facebook platform. Nothing fancy.
        """

        fb = Facebook()
        await fb.async_init()
        fb.on_message(self.fsm.handle_message)
        return fb

    async def get_platform(self, name: Text):
        """
        Get a valid instance of the specified platform. Do not cache this
        object, it might change with configuration changes.
        """

        if not self._is_init:
            await self.init()

        if name not in self.platforms:
            build = getattr(self, 'build_{}'.format(name), None)

            if not build:
                raise PlatformDoesNotExist('Platform "{}" does not exist'
                                           .format(name))

            self.platforms[name] = await build()

        return self.platforms[name]
