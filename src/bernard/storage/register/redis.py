import asyncio
from typing import Any, Dict, Text

import ujson

from bernard.conf import settings

from ..redis import BaseRedisStore
from .base import BaseRegisterStore


class RedisRegisterStore(BaseRedisStore, BaseRegisterStore):
    """
    Store the register in Redis.

    So far it is quite basic, especially regarding the locking mechanism which
    is just the bare minimum. This should seriously be improved in the future.
    """

    def lock_key(self, key: Text) -> Text:
        """
        Compute the internal lock key for the specified key
        """
        return "register::lock:{}".format(key)

    def register_key(self, key: Text) -> Text:
        """
        Compute the internal register content key for the specified key
        """
        return "register::content:{}".format(key)

    async def _start(self, key: Text) -> None:
        """
        Start the lock.

        Here we use a SETNX-based algorithm. It's quite shitty, change it.
        """
        for _ in range(0, 1000):
            just_set = await self.redis.setnx(self.lock_key(key), "")

            if just_set:
                break

            await asyncio.sleep(settings.REDIS_POLL_INTERVAL)

    async def _finish(self, key: Text) -> None:
        """
        Remove the lock.
        """

        await self.redis.delete(self.lock_key(key))

    async def _get(self, key: Text) -> Dict[Text, Any]:
        """
        Get the value for the key. It is automatically deserialized from JSON
        and returns an empty dictionary by default.
        """

        try:
            return ujson.loads(await self.redis.get(self.register_key(key)))
        except (ValueError, TypeError):
            return {}

    async def _replace(self, key: Text, data: Dict[Text, Any]) -> None:
        """
        Replace the register with a new value.
        """

        await self.redis.set(self.register_key(key), ujson.dumps(data))
