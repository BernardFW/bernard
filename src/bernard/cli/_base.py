# coding: utf-8
import logging

logger = logging.getLogger('bernard.cli')


def init_uvloop():
    import asyncio
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def init_logger():
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
    )


def init_live_reload(run):
    """
    Start the live reload task

    :param run: run the task inside of this function or just create it
    """
    from asyncio import get_event_loop
    from ._live_reload import start_child

    loop = get_event_loop()

    if run:
        loop.run_until_complete(start_child())
    else:
        get_event_loop().create_task(start_child())


def main():
    init_logger()
    init_uvloop()

    from bernard.conf import settings
    from os import getenv

    if settings.CODE_LIVE_RELOAD and getenv('_IN_CHILD') != 'yes':
        from ._live_reload import start_parent
        return start_parent()

    # noinspection PyBroadException
    try:
        from aiohttp import web
        from bernard.server import app
        from bernard.utils import run
        from bernard.platforms import start_all

        run(start_all())

        if settings.CODE_LIVE_RELOAD:
            init_live_reload(False)
    except Exception:
        logger.exception('Something bad happened while bootstraping')

        if settings.CODE_LIVE_RELOAD:
            init_live_reload(True)
    else:
        # noinspection PyArgumentList
        web.run_app(app, **settings.SERVER_BIND)
