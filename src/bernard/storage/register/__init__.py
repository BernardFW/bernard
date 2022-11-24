from .base import BaseRegisterStore, Register

try:
    # noinspection PyUnresolvedReferences
    from .redis import RedisRegisterStore
except ImportError:
    pass
