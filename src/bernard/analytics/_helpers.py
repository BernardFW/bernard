# coding: utf-8
from functools import wraps
from bernard.engine.state import BaseState

from bernard.analytics.base import providers


def page_view(url):
    """
    Page view decorator.

    Put that around a state handler function in order to log a page view each
    time the handler gets called.

    :param url: simili-URL that you want to give to the state
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self: BaseState, *args, **kwargs):
            user_id = self.request.user.id

            try:
                user_lang = await self.request.user.get_locale()
            except NotImplementedError:
                user_lang = ''

            title = self.__class__.__name__

            # noinspection PyTypeChecker
            async for p in providers():
                await p.page_view(url, title, user_id, user_lang)

            return await func(self, *args, **kwargs)
        return wrapper
    return decorator

