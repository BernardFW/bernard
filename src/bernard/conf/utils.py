# coding: utf-8
import os
from bernard.conf import settings
from contextlib import contextmanager
from ..conf import ENVIRONMENT_VARIABLE


def reload_config() -> None:
    """
    Reload the whole configuration.
    """

    # noinspection PyProtectedMember
    settings._reload()


@contextmanager
def patch_conf(settings_patch):
    """
    Reload the configuration form scratch. Only the default config is loaded,
    not the environment-specified config.

    Then the specified patch is applied.

    This is for unit tests only!

    :param settings_patch: Custom configuration values to insert
    """

    reload_config()
    os.environ[ENVIRONMENT_VARIABLE] = ''

    from bernard.conf import settings as l_settings
    # noinspection PyProtectedMember
    r_settings = l_settings._settings
    r_settings.update(settings_patch)
    yield
