"""Reference / instrument search — Postgres backed."""
from __future__ import annotations

from typing import Optional

from contracts.schema import Instrument, InstrumentList, utc_now_iso
from domain import db


def _row_to_instrument(row: dict) -> Instrument:
    return Instrument(
        symbol=row["symbol"],
        name=row["name"],
        market=row["market"],
        exchange=row.get("exchange"),
        currency=row.get("currency"),
        asset_class=row.get("asset_class"),
        active=bool(row.get("active", True)),
        as_of=utc_now_iso(),
        source="postgres",
        stale=False,
    )


def list_instruments(
    market: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> InstrumentList:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    clauses = ["active = TRUE"]
    params: list = []
    if market:
        clauses.append("market = %s")
        params.append(market.upper())
    if q:
        clauses.append("(symbol ILIKE %s OR name ILIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])
    where = " AND ".join(clauses)
    total_row = db.fetch_one(f"SELECT COUNT(*) AS n FROM instruments WHERE {where}", tuple(params))
    total = int(total_row["n"]) if total_row else 0
    params.extend([limit, offset])
    rows = db.fetch_all(
        f"""
        SELECT symbol, name, market, exchange, currency, asset_class, active
        FROM instruments
        WHERE {where}
        ORDER BY symbol
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    )
    items = [_row_to_instrument(r) for r in rows]
    return InstrumentList(items=items, total=total)


def search_instruments(q: str, market: Optional[str] = None, limit: int = 20) -> InstrumentList:
    return list_instruments(market=market, q=q, limit=limit, offset=0)
