"""Redis client wrapper."""
from __future__ import annotations

import os
from typing import Optional

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client
