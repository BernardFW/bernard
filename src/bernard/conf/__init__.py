# coding: utf-8
"""
Settings management.

This module is really inspired by the Django and the Sanic config systems,
thanks to their teams.
"""
import os
from typing import List, Text
from .loader import LazySettings

ENVIRONMENT_VARIABLE = 'BERNARD_SETTINGS_FILE'


def list_config_files() -> List[Text]:
    """
    This function returns the list of configuration files to load.

    This is a callable so the configuration can be reloaded with files that
    changed in between.
    """

    return [
        os.path.join(os.path.dirname(__file__), 'default_settings.py'),
        os.getenv(ENVIRONMENT_VARIABLE, ''),
    ]


settings = LazySettings(list_config_files)
