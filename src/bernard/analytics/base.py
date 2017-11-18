# coding: utf-8
from hashlib import sha256
from functools import wraps
from asyncio import get_event_loop
from typing import Dict, Tuple, Any

from bernard.utils import import_class
from bernard.conf import settings


class BaseAnalytics(object):
    """
    Standard interface for analytics tracking. If your platform doesn't support
    some operations, either adapt the concept, either make make the function
    empty and document it.
    """

    _instances: Dict[Tuple[Any, ...], 'BaseAnalytics'] = {}

    async def async_init(self):
        pass

    async def page_view(self,
                        url: str,
                        title: str,
                        user_id: str,
                        user_lang: str='') -> None:
        """
        Track the view of a page
        """

        raise NotImplementedError

    def hash_user_id(self, user_id: str) -> str:
        """
        As per the law, anonymize user identifier before sending it.
        """

        h = sha256()
        h.update(user_id.encode())
        return h.hexdigest()

    @classmethod
    async def instance(cls, *args) -> 'BaseAnalytics':
        if args not in cls._instances:
            cls._instances[args] = cls(*args)
            await cls._instances[args].async_init()
        return cls._instances[args]


def new_task(func):
    """
    Runs the decorated function in a new task
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        loop = get_event_loop()
        loop.create_task(func(self, *args, **kwargs))
    return wrapper


async def providers():
    """
    Iterates over all instances of analytics provider found in configuration
    """

    for provider in settings.ANALYTICS_PROVIDERS:
        cls: BaseAnalytics = import_class(provider['class'])
        yield await cls.instance(*provider['args'])
