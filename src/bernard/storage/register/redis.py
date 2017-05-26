# coding: utf-8
import aioredis
import asyncio
import ujson
from typing import Text, Any, Dict
from bernard.utils import run
from bernard.conf import settings
from .base import BaseRegisterStore


class RedisRegisterStore(BaseRegisterStore):
    """
    Store the register in Redis.

    So far it is quite basic, especially regarding the locking mechanism which
    is just the bare minimum. This should seriously be improved in the future.
    """

    def __init__(self,
                 host: Text='localhost',
                 port: int=6379,
                 db_id: int=0,
                 min_pool_size: int=5,
                 max_pool_size: int=10):
        """
        Give here the connection parameters to the redis. There is going to be
        a connection pool, so you can specify its size tool.

        Please note that this should be executed outside of an asyncio loop.

        :param host: IP/DNS host 
        :param port: TCP port
        :param db_id: ID of the DB
        :param min_pool_size: minimum number of connections alive
        :param max_pool_size: maximum number of connections alive
        """

        self.host = host
        self.port = port
        self.db_id = db_id
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.pool = None

    async def async_init(self):
        """
        Handle here the asynchronous part of the init.
        """

        self.pool = await aioredis.create_pool(
            (self.host, self.port),
            db=self.db_id,
            minsize=self.min_pool_size,
            maxsize=self.max_pool_size,
            loop=asyncio.get_event_loop(),
        )

    def lock_key(self, key: Text) -> Text:
        """
        Compute the internal lock key for the specified key
        """
        return 'register::lock:{}'.format(key)

    def register_key(self, key: Text) -> Text:
        """
        Compute the internal register content key for the specified key
        """
        return 'register::content:{}'.format(key)

    async def _start(self, key: Text) -> None:
        """
        Start the lock.

        Here we use a SETNX-based algorithm. It's quite shitty, change it. 
        """
        for _ in range(0, 1000):
            with await self.pool as r:
                just_set = await r.set(
                    self.lock_key(key),
                    '',
                    expire=settings.REGISTER_LOCK_TIME,
                    exist=r.SET_IF_NOT_EXIST,
                )

                if just_set:
                    break

            await asyncio.sleep(settings.REDIS_POLL_INTERVAL)

    async def _finish(self, key: Text) -> None:
        """
        Remove the lock.
        """

        with await self.pool as r:
            await r.delete(self.lock_key(key))

    async def _get(self, key: Text) -> Dict[Text, Any]:
        """
        Get the value for the key. It is automatically deserialized from JSON
        and returns an empty dictionary by default.
        """

        try:
            with await self.pool as r:
                return ujson.loads(await r.get(self.register_key(key)))
        except (ValueError, TypeError):
            return {}

    async def _replace(self, key: Text, data: Dict[Text, Any]) -> None:
        """
        Replace the register with a new value.
        """

        with await self.pool as r:
            await r.set(self.register_key(key), ujson.dumps(data))
