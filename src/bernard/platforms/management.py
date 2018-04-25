# coding: utf-8
import logging
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Optional,
    Text,
    Tuple,
    Type,
)

from bernard.conf import (
    settings,
)
from bernard.core.health_check import (
    HealthCheckFail,
)
from bernard.engine.fsm import (
    FSM,
)
from bernard.engine.platform import (
    Platform,
    PlatformDoesNotExist,
)
from bernard.engine.request import (
    BaseMessage,
)
from bernard.middleware import (
    MiddlewareManager,
)
from bernard.utils import (
    import_class,
)

logger = logging.getLogger('bernard.platform.health')


def get_platform_settings():
    """
    Returns the content of `settings.PLATFORMS` with a twist.

    The platforms settings was created to stay compatible with the old way of
    declaring the FB configuration, in order not to break production bots. This
    function will convert the legacy configuration into the new configuration
    if required. As a result, it should be the only used way to access the
    platform configuration.
    """

    s = settings.PLATFORMS

    if hasattr(settings, 'FACEBOOK') and settings.FACEBOOK:
        s.append({
            'class': 'bernard.platforms.facebook.platform.Facebook',
            'settings': settings.FACEBOOK,
        })

    return s


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
        self._classes = self._index_classes()

    @property
    def _is_init(self):
        """
        Check if initialization was done
        """
        return self.fsm is not None

    async def init(self):
        """
        Creates the FSM and the cache. It can be called several times to reset
        stuff (like for unit tests...).

        It also runs all the health checks in order to see if everything is fit
        for running.
        """
        self.fsm = FSM()

        checks = []

        # noinspection PyTypeChecker
        async for check in self.run_checks():
            checks.append(check)
            logger.error('HEALTH CHECK FAIL #%s: %s', check.code, check.reason)

        if checks:
            exit(1)

        await self.fsm.async_init()

        self.platforms = {}

    async def run_checks(self):
        """
        Run checks on itself and on the FSM
        """

        async for check in self.fsm.health_check():
            yield check

        async for check in self.self_check():
            yield check

        for check in MiddlewareManager.health_check():
            yield check

    async def self_check(self):
        """
        Checks that the platforms configuration is all right.
        """

        platforms = set()

        for platform in get_platform_settings():
            try:
                name = platform['class']
                cls: Type[Platform] = import_class(name)
            except KeyError:
                yield HealthCheckFail(
                    '00004',
                    'Missing platform `class` name in configuration.'
                )
            except (AttributeError, ImportError, ValueError):
                yield HealthCheckFail(
                    '00003',
                    f'Platform "{name}" cannot be imported.'
                )
            else:
                if cls in platforms:
                    yield HealthCheckFail(
                        '00002',
                        f'Platform "{name}" is imported more than once.'
                    )
                platforms.add(cls)

                # noinspection PyTypeChecker
                async for check in cls.self_check():
                    yield check

    def _index_classes(self) -> Dict[Text, Type[Platform]]:
        """
        Build a name index for all platform classes
        """

        out = {}

        for p in get_platform_settings():
            cls: Type[Platform] = import_class(p['class'])

            if 'name' in p:
                out[p['name']] = cls
            else:
                out[cls.NAME] = cls

        return out

    async def build_platform(self, cls: Type[Platform], custom_id):
        """
        Build the Facebook platform. Nothing fancy.
        """

        from bernard.server.http import router

        p = cls()

        if custom_id:
            p._id = custom_id

        await p.async_init()
        p.on_message(self.fsm.handle_message)
        p.hook_up(router)
        return p

    def get_class(self, platform) -> Type[Platform]:
        """
        For a given platform name, gets the matching class
        """

        if platform in self._classes:
            return self._classes[platform]

        raise PlatformDoesNotExist('Platform "{}" is not in configuration'
                                   .format(platform))

    async def get_platform(self, name: Text):
        """
        Get a valid instance of the specified platform. Do not cache this
        object, it might change with configuration changes.
        """

        if not self._is_init:
            await self.init()

        if name not in self.platforms:
            self.platforms[name] = \
                await self.build_platform(self.get_class(name), name)

        return self.platforms[name]

    async def get_all_platforms(self) -> AsyncIterator[Platform]:
        """
        Returns all platform instances
        """

        for name in self._classes.keys():
            yield await self.get_platform(name)

    async def message_from_token(self, token: Text, payload: Any) \
            -> Tuple[Optional[BaseMessage], Optional[Platform]]:
        """
        Given an authentication token, find the right platform that can
        recognize this token and create a message for this platform.

        The payload will be inserted into a Postback layer.
        """

        async for platform in self.get_all_platforms():
            m = await platform.message_from_token(token, payload)

            if m:
                return m, platform

        return None, None
