"""Readiness checks for Postgres + Redis."""
from __future__ import annotations

from typing import Any


def check_ready() -> dict[str, Any]:
    postgres_ok = False
    redis_ok = False
    failures: list[str] = []
    details: dict[str, str] = {}

    try:
        from domain import db

        row = db.fetch_one("SELECT 1 AS ok")
        postgres_ok = bool(row and row.get("ok") == 1)
        if not postgres_ok:
            failures.append("postgres")
            details["postgres"] = "unexpected response"
        else:
            details["postgres"] = "ok"
    except Exception as e:
        failures.append("postgres")
        details["postgres"] = str(e)

    try:
        from domain.redis_client import get_redis

        pong = get_redis().ping()
        redis_ok = bool(pong)
        if not redis_ok:
            failures.append("redis")
            details["redis"] = "ping failed"
        else:
            details["redis"] = "ok"
    except Exception as e:
        failures.append("redis")
        details["redis"] = str(e)

    ok = postgres_ok and redis_ok
    return {
        "status": "ok" if ok else "unavailable",
        "postgres": postgres_ok,
        "redis": redis_ok,
        "failed": failures,
        "details": details,
        "service": "omnialpha",
    }
