# coding: utf-8
from typing import TYPE_CHECKING, Text

if TYPE_CHECKING:
    from bernard.engine.request import Request


class BaseReporter(object):
    """
    This is the base class that reports errors
    """

    def report(self, request: 'Request'=None, state: Text=None):
        """
        Report an error to the reporting system. Give as much context as
        possible.
        """
        raise NotImplementedError
