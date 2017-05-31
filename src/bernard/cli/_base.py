# coding: utf-8


def init_uvloop():
    import asyncio
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def init_logger():
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
    )


def main():
    init_logger()
    init_uvloop()

    from aiohttp import web
    from bernard.server import app
    from bernard.conf import settings
    from bernard.utils import run
    from bernard.platforms import start_all

    run(start_all())

    # noinspection PyArgumentList
    web.run_app(app, **settings.SERVER_BIND)
