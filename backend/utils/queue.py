"""
Redis-backed queue helpers.

Uses redis-py's async client.  Each queue is a simple Redis list;
producers LPUSH, consumers BRPOP (blocking right-pop) so they wake
up immediately when work arrives.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def enqueue(queue_name: str, payload: dict[str, Any]) -> None:
    """Push *payload* onto the left of *queue_name*."""
    client = get_redis()
    await client.lpush(queue_name, json.dumps(payload))
    logger.debug("Enqueued to %s: %s", queue_name, str(payload)[:80])


async def dequeue(queue_name: str, timeout: int = 5) -> dict[str, Any] | None:
    """
    Blocking pop from *queue_name*.
    Returns None on timeout (allows the worker loop to check a stop flag).
    """
    client = get_redis()
    result = await client.brpop(queue_name, timeout=timeout)
    if result is None:
        return None
    _queue, raw = result
    return json.loads(raw)


async def queue_length(queue_name: str) -> int:
    client = get_redis()
    return await client.llen(queue_name)


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
