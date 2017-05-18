# coding: utf-8
"""
Settings management.

This module is really inspired by the Django and the Sanic config systems,
thanks to their teams.
"""
import os
from .loader import LazySettings

ENVIRONMENT_VARIABLE = 'BERNARD_SETTINGS_FILE'


settings = LazySettings([
    os.path.join(os.path.dirname(__file__), 'default_settings.py'),
    os.getenv(ENVIRONMENT_VARIABLE, ''),
])
