# coding: utf-8
from typing import TYPE_CHECKING, Text
from raven import Client
from raven_aiohttp import AioHttpTransport
from bernard.conf import settings
from bernard.utils import make_rw
from ._base import BaseReporter

if TYPE_CHECKING:
    from bernard.engine.request import Request


class RavenReporter(BaseReporter):
    """
    Report errors to Raven
    """

    def __init__(self):
        self.client = Client(
            transport=AioHttpTransport,
            dsn=settings.SENTRY_DSN,
        )

    def _make_context(self, request: 'Request'=None, state: Text=None):
        """
        Build the context for a specific request/state
        """

        if request:
            self.client.user_context({
                'id': request.user.id,
            })
            self.client.extra_context({
                'message': repr(request.stack),
                'register': make_rw(request.register),
            })
            self.client.tags_context({
                'conversation_id': request.conversation.id,
                'from_state': request.register.get(request.register.STATE),
                'state': state,
                'platform': request.platform,
            })

    def _clear_context(self):
        """
        Clear the context awaiting next call
        :return: 
        """

        self.client.context.clear()

    def report(self, request: 'Request'=None, state: Text=None):
        """
        Report current exception to Sentry.
        """
        self._make_context(request, state)
        self.client.captureException()
        self._clear_context()
