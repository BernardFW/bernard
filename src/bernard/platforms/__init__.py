# coding: utf-8
from .management import PlatformManager

manager = PlatformManager()

async def start_all():
    """
    A utility function for the CLI to start all platforms directly and not
    lazily wait for them to start.
    """

    await manager.get_platform('facebook')
