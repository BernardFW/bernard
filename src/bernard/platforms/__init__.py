# coding: utf-8
from typing import Type

from .management import PlatformManager, get_platform_settings
from ..utils import import_class
from ..engine.platform import Platform, SimplePlatform

manager = PlatformManager()


async def start_all():
    """
    A utility function for the CLI to start all platforms directly and not
    lazily wait for them to start.
    """

    await manager.init()

    async for _ in manager.get_all_platforms():
        pass
