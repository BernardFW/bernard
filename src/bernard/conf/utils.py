# coding: utf-8
import sys


def reload_config() -> None:
    """
    Reload the config module. You need to re-import the module afterwards for
    this to take effect.
    """

    if 'bernard.conf' in sys.modules:
        del sys.modules['bernard.conf']
