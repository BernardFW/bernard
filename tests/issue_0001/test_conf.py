import os

import pytest

from bernard.conf import ENVIRONMENT_VARIABLE
from bernard.conf.loader import LazySettings, Settings
from bernard.conf.utils import reload_config

asset_config_path = os.path.join(
    os.path.dirname(__file__),
    "assets",
    "settings.py",
)


def test_load_file():
    settings = Settings()
    # noinspection PyProtectedMember
    settings._load(asset_config_path)

    assert settings.FOO == "bar"
    assert settings.BAR == [1, 2, 3]


def test_lazy_load_file():
    settings = LazySettings(lambda: [asset_config_path])

    assert settings.FOO == "bar"
    assert settings.BAR == [1, 2, 3]


def test_set_settings():
    settings = Settings()
    settings.NEW_KEY = "new_value"
    assert settings.NEW_KEY == "new_value"


def test_set_lazy_settings():
    settings = LazySettings(lambda: [])
    settings.NEW_KEY = "new_value"
    assert settings.NEW_KEY == "new_value"


def test_load_missing_file():
    settings = Settings()
    file_path = "/does/not/exist/62c889d0-39a0-4f5b-838b-abb635dee5fc.txt"

    with pytest.raises(IOError):
        # noinspection PyProtectedMember
        settings._load(file_path)


def test_read_missing_key():
    settings = Settings()

    with pytest.raises(AttributeError):
        assert settings.DOES_NOT_EXIST


def test_reload_config():
    from bernard.conf import settings

    settings.NEWLY_SET = True
    assert settings.NEWLY_SET

    reload_config()

    with pytest.raises(AttributeError):
        assert settings.NEWLY_SET


def test_loads_environment_file():
    os.environ[ENVIRONMENT_VARIABLE] = asset_config_path
    reload_config()

    from bernard.conf import settings

    assert settings.FOO == "bar"


def test_loads_default_conf():
    os.environ[ENVIRONMENT_VARIABLE] = ""
    reload_config()

    from bernard.conf import settings

    assert isinstance(settings.DEBUG, bool)
