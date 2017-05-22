# coding: utf-8
import os
from sys import modules
from bernard.conf import settings
from contextlib import contextmanager
from ..conf import ENVIRONMENT_VARIABLE


def reload_config() -> None:
    """
    Reload the whole configuration.
    """

    # noinspection PyProtectedMember
    settings._reload()


# noinspection PyProtectedMember
@contextmanager
def patch_conf(settings_patch=None, settings_file=None):
    """
    Reload the configuration form scratch. Only the default config is loaded,
    not the environment-specified config.

    Then the specified patch is applied.

    This is for unit tests only!

    :param settings_patch: Custom configuration values to insert
    """

    if settings_patch is None:
        settings_patch = {}

    reload_config()
    os.environ[ENVIRONMENT_VARIABLE] = settings_file if settings_file else ''

    from bernard.conf import settings as l_settings
    # noinspection PyProtectedMember
    r_settings = l_settings._settings
    r_settings.update(settings_patch)

    if 'bernard.i18n' in modules:
        from bernard.i18n import translate, intents
        translate._regenerate_word_dict()
        intents._refresh_intents_db()

    yield
