# coding: utf-8
from typing import Text
import ujson
from .base import BaseContextStore, Context
from ..redis import BaseRedisStore


class RedisContextStore(BaseRedisStore, BaseContextStore):
    """
    Store the context as a serialized JSON inside Redis. It's made to be
    compatible with the register storage, if using the same Redis DB.
    """

    async def _get(self, key: Text) -> Context:
        try:
            with await self.pool as r:
                return ujson.loads(await r.get(key))
        except (ValueError, TypeError):
            return {}

    async def _set(self, key: Text, data: Context) -> None:
        with await self.pool as r:
            await r.set(key, ujson.dumps(data), expire=self.ttl)
