from math import ceil
from typing import Any

from fastapi import Request, Response
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from redis import asyncio as aioredis  # type: ignore

from src.core.config import settings


async def init_rate_limiter() -> None:
    redis = await aioredis.from_url(
        str(settings.REDIS_URL), encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis)


def rate_limit_callback(request: Request, response: Response, pexpire: int) -> None:
    """
    Callback for when a rate limit is exceeded.
    Adds headers to the response indicating the limit status.
    """
    expire = ceil(pexpire / 1000)
    raise ValueError("Too Many Requests")


def get_rate_limiter(times: int, seconds: int):
    """
    Get a rate limiter dependency that's disabled in testing environment.

    Checks environment at runtime to support testing.

    Args:
        times: Number of requests allowed
        seconds: Time window in seconds

    Returns:
        Runtime-checking rate limiter dependency
    """
    class RuntimeRateLimiter:
        """Rate limiter that checks environment at runtime."""

        def __init__(self):
            self.times = times
            self.seconds = seconds
            self._real_limiter = None

        async def __call__(self, request: Request, response: Response):
            # Check environment at runtime, not at import time
            if settings.RATE_LIMIT_ENABLED:
                # Lazy initialization of real rate limiter
                if self._real_limiter is None:
                    self._real_limiter = RateLimiter(times=self.times, seconds=self.seconds)
                await self._real_limiter(request, response)
            # else: no-op for testing

    return RuntimeRateLimiter()
