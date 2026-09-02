"""US quotes/bars via yfinance (Yahoo Finance)."""
from __future__ import annotations

import logging
from datetime import timezone
from typing import Optional

from contracts.schema import Bar, Quote, SymbolId, utc_now_iso

log = logging.getLogger(__name__)
SOURCE = "yfinance"


def _ticker(sid: SymbolId):
    try:
        import yfinance as yf
    except ImportError as e:
        raise RuntimeError(
            "yfinance not installed; add yfinance to requirements and rebuild"
        ) from e

    if sid.prefix != "US":
        raise ValueError("us adapter only supports US symbols")
    return yf.Ticker(sid.code)


def fetch_quote(sid: SymbolId) -> Quote:
    t = _ticker(sid)
    info = {}
    try:
        info = t.fast_info or {}
    except Exception as e:
        log.warning("yfinance fast_info failed for %s: %s", sid.canonical, e)
    last: Optional[float] = None
    for key in ("lastPrice", "last_price", "regularMarketPrice"):
        val = info.get(key) if isinstance(info, dict) else getattr(info, key, None)
        if val is not None:
            try:
                last = float(val)
                break
            except (TypeError, ValueError):
                pass
    if last is None:
        hist = t.history(period="5d", interval="1d")
        if hist is None or hist.empty:
            raise RuntimeError(f"yfinance: no quote data for {sid.canonical}")
        last = float(hist["Close"].iloc[-1])
        open_ = float(hist["Open"].iloc[-1])
        high = float(hist["High"].iloc[-1])
        low = float(hist["Low"].iloc[-1])
        volume = float(hist["Volume"].iloc[-1]) if "Volume" in hist else None
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else None
        name = sid.code
    else:
        def _f(k: str) -> Optional[float]:
            v = info.get(k) if isinstance(info, dict) else getattr(info, k, None)
            try:
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        open_ = _f("open") or _f("regularMarketOpen")
        high = _f("dayHigh") or _f("regularMarketDayHigh")
        low = _f("dayLow") or _f("regularMarketDayLow")
        volume = _f("lastVolume") or _f("regularMarketVolume")
        prev_close = _f("previousClose") or _f("regularMarketPreviousClose")
        name = sid.code
        try:
            meta = t.info or {}
            if isinstance(meta, dict) and meta.get("shortName"):
                name = str(meta["shortName"])
        except Exception:
            pass

    change = (last - prev_close) if prev_close is not None else None
    change_pct = ((change / prev_close) * 100.0) if change is not None and prev_close else None
    return Quote(
        symbol=sid.canonical,
        last=last,
        open=open_,
        high=high,
        low=low,
        prev_close=prev_close,
        volume=volume,
        change=change,
        change_pct=change_pct,
        name=name,
        as_of=utc_now_iso(),
        source=SOURCE,
        stale=False,
    )


def _interval_map(interval: str) -> tuple[str, str]:
    """Return (yf_interval, period)."""
    mapping = {
        "1d": ("1d", "3mo"),
        "day": ("1d", "3mo"),
        "1h": ("1h", "1mo"),
        "60m": ("1h", "1mo"),
        "1m": ("1m", "5d"),
        "5m": ("5m", "5d"),
        "15m": ("15m", "5d"),
        "30m": ("30m", "1mo"),
        "1w": ("1wk", "1y"),
        "week": ("1wk", "1y"),
    }
    key = interval.strip()
    if key not in mapping:
        raise ValueError(f"unsupported interval '{interval}' for yfinance")
    return mapping[key]


def fetch_bars(sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]:
    t = _ticker(sid)
    yf_interval, period = _interval_map(interval)
    limit = max(1, min(limit, 500))
    hist = t.history(period=period, interval=yf_interval)
    if hist is None or hist.empty:
        return []
    hist = hist.tail(limit)
    bars: list[Bar] = []
    as_of = utc_now_iso()
    for idx, row in hist.iterrows():
        ts = idx.to_pydatetime()
        if ts.tzinfo is None:
            open_time = ts.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        else:
            open_time = ts.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        bars.append(
            Bar(
                symbol=sid.canonical,
                interval=interval,
                open_time=open_time,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]) if "Volume" in row and row["Volume"] == row["Volume"] else None,
                as_of=as_of,
                source=SOURCE,
                stale=False,
            )
        )
    return bars



class UsYfinanceAdapter:
    market = "US"

    def fetch_quote(self, sid: SymbolId) -> Quote:
        return fetch_quote(sid)

    def fetch_bars(self, sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]:
        return fetch_bars(sid, interval=interval, limit=limit)
