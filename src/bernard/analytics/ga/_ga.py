# coding: utf-8
import logging
from urllib.parse import urlencode
from aiohttp import ClientSession
from ..base import BaseAnalytics, new_task


logger = logging.getLogger('bernard.analytics.ga')


class GoogleAnalytics(BaseAnalytics):
    """
    A class that speaks the Measurement Protocol in order to log conversations
    inside GA.

    This is a singleton, you need to call the static `instance()` method to
    get your instance.
    """

    def __init__(self, ga_id, ga_domain):
        self.session = None
        self.ga_id = ga_id
        self.ga_domain = ga_domain

    async def async_init(self):
        self.session = ClientSession()

    @new_task
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
        :param user_lang: Current language of the UI.
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
