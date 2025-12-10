from math import ceil

from fastapi import Request, Response
from fastapi_limiter import FastAPILimiter
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
