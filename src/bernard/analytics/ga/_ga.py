# coding: utf-8
import logging
from hashlib import sha256
from functools import wraps
from urllib.parse import urlencode
from aiohttp import ClientSession
from asyncio import get_event_loop
from bernard.conf import settings


logger = logging.getLogger('bernard.analytics.ga')


def run_ga(func):
    """
    Internal helper to only run Google Analytics-logging functions when it is
    configured. Also starts the logging in a separate task, as we don't want
    to slow down the main execution with analytics.
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.ga_id and self.ga_domain:
            loop = get_event_loop()
            loop.create_task(func(self, *args, **kwargs))
    return wrapper


class GoogleAnalytics(object):
    """
    A class that speaks the Measurement Protocol in order to log conversations
    inside GA.

    This is a singleton, you need to call the static `instance()` method to
    get your instance.
    """

    _instance = None  # type: GoogleAnalytics

    def __init__(self):
        self.session = None
        self.ga_id = settings.GOOGLE_ANALYTICS_ID
        self.ga_domain = settings.GOOGLE_ANALYTICS_DOMAIN

    async def async_init(self):
        self.session = ClientSession()

    @classmethod
    async def instance(cls) -> 'GoogleAnalytics':
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance.async_init()
        # noinspection PyTypeChecker
        return cls._instance

    def hash_user_id(self, user_id: str) -> str:
        """
        As per the law, anonymize user identifier before sending it.
        """

        h = sha256()
        h.update(user_id.encode())
        h.update(self.ga_id.encode())
        h.update(self.ga_domain.encode())
        return h.hexdigest()

    @run_ga
    async def page_view(self,
                        url: str,
                        title: str,
                        user_id: str,
                        user_lang: str='') -> None:
        """
        Log a page view.

        :param url: URL of the "page"
        :param title: Title of the "page"
        :param user_id: ID of the user seeing the page.
        """
        ga_url = 'https://www.google-analytics.com/collect'

        args = {
            'v': '1',
            'ds': 'web',
            'de': 'UTF-8',
            'tid': self.ga_id,
            'cid': self.hash_user_id(user_id),

            't': 'pageview',
            'dh': self.ga_domain,
            'dp': url,
            'dt': title,
        }

        if user_lang:
            args['ul'] = user_lang

        logger.debug('GA settings = %s', urlencode(args))

        async with self.session.post(ga_url, data=args) as r:
            if r.status == 200:
                logger.debug(f'Sent to GA {url} ({title}) for user {user_id}')
            else:
                logger.warning(f'Could not contact GA')
