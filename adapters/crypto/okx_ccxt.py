"""CRYPTO quotes/bars via ccxt OKX public API."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from contracts.schema import Bar, Quote, SymbolId, utc_now_iso

log = logging.getLogger(__name__)
SOURCE = "okx-ccxt"

_exchange = None


def _get_exchange():
    global _exchange
    if _exchange is None:
        import ccxt

        _exchange = ccxt.okx({"enableRateLimit": True})
    return _exchange


def to_ccxt_symbol(sid: SymbolId) -> str:
    """CRYPTO:BTCUSDT -> BTC/USDT; CRYPTO:BTC/USDT -> BTC/USDT."""
    if sid.prefix != "CRYPTO":
        raise ValueError("crypto adapter only supports CRYPTO symbols")
    code = sid.code.upper()
    if "/" in code:
        return code
    # Common compact forms: BTCUSDT, ETHUSDT, BTC-USDT
    code = code.replace("-", "")
    for quote in ("USDT", "USD", "USDC", "BTC", "ETH"):
        if code.endswith(quote) and len(code) > len(quote):
            base = code[: -len(quote)]
            return f"{base}/{quote}"
    raise ValueError(f"cannot map CRYPTO code '{sid.code}' to ccxt symbol")


def fetch_quote(sid: SymbolId) -> Quote:
    ex = _get_exchange()
    symbol = to_ccxt_symbol(sid)
    ticker: dict[str, Any] = ex.fetch_ticker(symbol)
    last = float(ticker["last"])
    bid = float(ticker["bid"]) if ticker.get("bid") is not None else None
    ask = float(ticker["ask"]) if ticker.get("ask") is not None else None
    open_ = float(ticker["open"]) if ticker.get("open") is not None else None
    high = float(ticker["high"]) if ticker.get("high") is not None else None
    low = float(ticker["low"]) if ticker.get("low") is not None else None
    volume = float(ticker["baseVolume"]) if ticker.get("baseVolume") is not None else None
    prev = float(ticker["previousClose"]) if ticker.get("previousClose") is not None else None
    change = float(ticker["change"]) if ticker.get("change") is not None else None
    change_pct = float(ticker["percentage"]) if ticker.get("percentage") is not None else None
    return Quote(
        symbol=sid.canonical,
        last=last,
        bid=bid,
        ask=ask,
        open=open_,
        high=high,
        low=low,
        prev_close=prev,
        volume=volume,
        change=change,
        change_pct=change_pct,
        name=symbol,
        as_of=utc_now_iso(),
        source=SOURCE,
        stale=False,
    )


def _tf(interval: str) -> str:
    mapping = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "60m": "1h",
        "4h": "4h",
        "1d": "1d",
        "day": "1d",
        "1w": "1w",
        "week": "1w",
    }
    key = interval.strip()
    if key not in mapping:
        raise ValueError(f"unsupported interval '{interval}' for okx")
    return mapping[key]


def fetch_bars(sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]:
    ex = _get_exchange()
    symbol = to_ccxt_symbol(sid)
    limit = max(1, min(limit, 300))
    ohlcv = ex.fetch_ohlcv(symbol, timeframe=_tf(interval), limit=limit)
    as_of = utc_now_iso()
    bars: list[Bar] = []
    for row in ohlcv:
        ts_ms, o, h, l, c, v = row[0], row[1], row[2], row[3], row[4], row[5]
        open_time = (
            datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
        bars.append(
            Bar(
                symbol=sid.canonical,
                interval=interval,
                open_time=open_time,
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(c),
                volume=float(v) if v is not None else None,
                as_of=as_of,
                source=SOURCE,
                stale=False,
            )
        )
    return bars
