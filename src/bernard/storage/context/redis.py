from typing import Text

import ujson

from ..redis import BaseRedisStore
from .base import BaseContextStore, Context


class RedisContextStore(BaseRedisStore, BaseContextStore):
    """
    Store the context as a serialized JSON inside Redis. It's made to be
    compatible with the register storage, if using the same Redis DB.
    """

    async def _get(self, key: Text) -> Context:
        try:
            return ujson.loads(await self.redis.get(key))
        except (ValueError, TypeError):
            return {}

    async def _set(self, key: Text, data: Context) -> None:
        await self.redis.set(key, ujson.dumps(data), ex=self.ttl)
