#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : cache.py

from typing import Callable

from redis.asyncio import Redis
from package.redis.client import new_asyncio_redis_client


class AsyncRedisCache:

    def __init__(
        self,
        *,
        key: str,
        new_func: Callable[[], Redis] | None = None,
        timeout: int = None, # TODO: need default
    ):
        if new_func is None:
            new_func = new_asyncio_redis_client

        self.new_func = new_func
        self.key = f"kido:cache:{key}"
        self.timeout = timeout

    async def get(self) -> str | None:
        async with self.new_func() as redis_client:
            return await redis_client.get(self.key)

    async def set(self, value: str) -> None:
        async with self.new_func() as redis_client:
            await redis_client.set(self.key, value, ex=self.timeout)
