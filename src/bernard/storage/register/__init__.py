# coding: utf-8

from .base import Register, BaseRegisterStore

try:
    # noinspection PyUnresolvedReferences
    from .redis import RedisRegisterStore
except ImportError:
    pass
