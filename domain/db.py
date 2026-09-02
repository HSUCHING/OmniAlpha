"""Lightweight Postgres helpers (psycopg)."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://facade:facade@localhost:5432/facade",
)

SEED_INSTRUMENTS = [
    ("CN:600519", "贵州茅台", "CN", "SSE", "CNY", "equity"),
    ("CN:000001", "平安银行", "CN", "SZSE", "CNY", "equity"),
    ("CN:000858", "五粮液", "CN", "SZSE", "CNY", "equity"),
    ("CN:601318", "中国平安", "CN", "SSE", "CNY", "equity"),
    ("US:AAPL", "Apple Inc.", "US", "NASDAQ", "USD", "equity"),
    ("US:MSFT", "Microsoft Corp.", "US", "NASDAQ", "USD", "equity"),
    ("CRYPTO:BTCUSDT", "Bitcoin / USDT", "CRYPTO", "BINANCE", "USDT", "crypto"),
    ("CRYPTO:ETHUSDT", "Ethereum / USDT", "CRYPTO", "BINANCE", "USDT", "crypto"),
]


def get_conn() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5)


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS instruments (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                market TEXT NOT NULL,
                exchange TEXT,
                currency TEXT,
                asset_class TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        for row in SEED_INSTRUMENTS:
            conn.execute(
                """
                INSERT INTO instruments (symbol, name, market, exchange, currency, asset_class)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET
                    name = EXCLUDED.name,
                    market = EXCLUDED.market,
                    exchange = EXCLUDED.exchange,
                    currency = EXCLUDED.currency,
                    asset_class = EXCLUDED.asset_class
                """,
                row,
            )


def fetch_all(sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    with connection() as conn:
        cur = conn.execute(sql, params or ())
        return list(cur.fetchall())


def fetch_one(sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
    with connection() as conn:
        cur = conn.execute(sql, params or ())
        return cur.fetchone()
