# coding: utf-8
import string
from typing import Union, Text
from datetime import date, datetime, tzinfo
from dateutil.parser import parse as parse_date
from babel import dates


def make_date(obj: Union[date, datetime, Text], timezone: tzinfo=None):
    """
    A flexible method to get a date object.
    
    It accepts either an ISO 8601 date/time string, either a Python `datetime`,
    either a Python `date`.
    
    If the input is a date/time and a timezone is specified, the resulting
    date object will be in the specified time zone.
    """

    if isinstance(obj, datetime):
        if hasattr(obj, 'astimezone') and timezone:
            obj = obj.astimezone(timezone)
        return obj.date()
    elif isinstance(obj, date):
        return obj
    elif isinstance(obj, str):
        return make_date(parse_date(obj), timezone)


class I18nFormatter(string.Formatter):
    """
    That is a string formatter that is aware of locale/regional settings/etc,
    and provides special field formatters.

    Available:

        - `date:FORMAT`: format the date using Babel. The FORMAT is anything
          that Babel's `format_date()` would take.
    """

    def __init__(self, lang, timezone=None):
        self.lang = lang
        self.timezone = timezone

    def format_date(self, value, format_):
        """
        Format the date using Babel
        """
        date_ = make_date(value)
        return dates.format_date(date_, format_, locale=self.lang)

    def format_field(self, value, spec):
        """
        Provide the additional formatters for localization.
        """

        if spec.startswith('date:'):
            _, format_ = spec.split(':', 1)
            return self.format_date(value, format_)
        else:
            return super(I18nFormatter, self).format_field(value, spec)
