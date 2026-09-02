"""CRYPTO adapter via OKX public REST (httpx only)."""
from __future__ import annotations

import logging
import re
from typing import Optional

import httpx

from contracts.schema import Bar, Quote, SymbolId, utc_now_iso

log = logging.getLogger(__name__)
SOURCE = "okx"
BASE = "https://www.okx.com"
TICKER_PATH = "/api/v5/market/ticker"
CANDLES_PATH = "/api/v5/market/candles"


def to_okx_inst_id(sid: SymbolId) -> str:
    """Map CRYPTO:BTCUSDT -> BTC-USDT (insert dash before quote currency)."""
    if sid.prefix != "CRYPTO":
        raise ValueError("crypto adapter only supports CRYPTO symbols")
    code = sid.code.upper().replace("_", "").replace("-", "")
    for quote in ("USDT", "USDC", "USD", "BTC", "ETH"):
        if code.endswith(quote) and len(code) > len(quote):
            base = code[: -len(quote)]
            return f"{base}-{quote}"
    # already looks like BASE-QUOTE
    if "-" in sid.code:
        return sid.code.upper()
    raise ValueError(f"cannot map CRYPTO code '{sid.code}' to OKX instId")


def fetch_quote(sid: SymbolId, timeout: float = 8.0) -> Quote:
    inst_id = to_okx_inst_id(sid)
    url = f"{BASE}{TICKER_PATH}"
    with httpx.Client(timeout=timeout, headers={"User-Agent": "data-facade/0.1"}) as client:
        r = client.get(url, params={"instId": inst_id})
        r.raise_for_status()
        data = r.json()
    if str(data.get("code")) != "0":
        raise ValueError(f"okx ticker error: {data.get('msg') or data}")
    rows = data.get("data") or []
    if not rows:
        raise ValueError(f"okx ticker empty for {inst_id}")
    row = rows[0]
    last = float(row["last"])
    open24 = _f(row.get("open24h"))
    high = _f(row.get("high24h"))
    low = _f(row.get("low24h"))
    vol = _f(row.get("vol24h") or row.get("volCcy24h"))
    bid = _f(row.get("bidPx"))
    ask = _f(row.get("askPx"))
    # OKX does not give prev_close directly; approximate with open24h
    prev = open24
    change = (last - prev) if prev is not None else None
    change_pct = ((change / prev) * 100.0) if change is not None and prev else None
    return Quote(
        symbol=sid.canonical,
        last=last,
        bid=bid,
        ask=ask,
        open=open24,
        high=high,
        low=low,
        prev_close=prev,
        volume=vol,
        change=change,
        change_pct=change_pct,
        name=inst_id,
        as_of=utc_now_iso(),
        source=SOURCE,
        stale=False,
    )


def _interval_to_bar(interval: str) -> str:
    mapping = {
        "1d": "1D",
        "day": "1D",
        "1w": "1W",
        "week": "1W",
        "1h": "1H",
        "60m": "1H",
        "4h": "4H",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1m": "1m",
    }
    key = interval.strip()
    if key not in mapping:
        raise ValueError(f"unsupported interval '{interval}' for okx candles")
    return mapping[key]


def fetch_bars(sid: SymbolId, interval: str = "1d", limit: int = 5, timeout: float = 10.0) -> list[Bar]:
    inst_id = to_okx_inst_id(sid)
    bar = _interval_to_bar(interval)
    limit = max(1, min(limit, 300))
    url = f"{BASE}{CANDLES_PATH}"
    with httpx.Client(timeout=timeout, headers={"User-Agent": "data-facade/0.1"}) as client:
        r = client.get(url, params={"instId": inst_id, "bar": bar, "limit": str(limit)})
        r.raise_for_status()
        data = r.json()
    if str(data.get("code")) != "0":
        raise ValueError(f"okx candles error: {data.get('msg') or data}")
    rows = data.get("data") or []
    # OKX returns newest first: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
    bars: list[Bar] = []
    as_of = utc_now_iso()
    for row in reversed(rows[:limit]):
        if not row or len(row) < 5:
            continue
        ts_ms = int(row[0])
        open_time = _ms_iso(ts_ms)
        bars.append(
            Bar(
                symbol=sid.canonical,
                interval=interval,
                open_time=open_time,
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]) if len(row) > 5 and row[5] not in (None, "") else None,
                as_of=as_of,
                source=SOURCE,
                stale=False,
            )
        )
    return bars


def _f(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ms_iso(ts_ms: int) -> str:
    from datetime import datetime, timezone

    return (
        datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


class OkxCryptoAdapter:
    market = "CRYPTO"

    def fetch_quote(self, sid: SymbolId) -> Quote:
        return fetch_quote(sid)

    def fetch_bars(self, sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]:
        return fetch_bars(sid, interval=interval, limit=limit)
