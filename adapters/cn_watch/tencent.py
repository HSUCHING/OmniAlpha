"""Tencent finance quote + kline adapter (CN A-share). Domain must not import this SDK/HTTP."""
from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from contracts.schema import Bar, Quote, SymbolId, utc_now_iso

log = logging.getLogger(__name__)

QUOTE_URL = "https://qt.gtimg.cn/q={tencent_code}"
KLINE_URL = (
    "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    "?param={tencent_code},{period},,,{limit},qfq"
)

SOURCE = "tencent"


def to_tencent_code(sid: SymbolId) -> str:
    """Map CN:600519 -> sh600519, CN:000001 -> sz000001."""
    code = sid.code
    if not code.isdigit() or len(code) != 6:
        raise ValueError(f"CN code must be 6 digits, got {code}")
    # SSE: 5xxxxx, 6xxxxx, 9xxxxx; SZSE: 0xxxxx, 1xxxxx, 2xxxxx, 3xxxxx
    if code.startswith(("5", "6", "9")):
        return f"sh{code}"
    return f"sz{code}"


def _parse_quote_body(body: str, sid: SymbolId) -> Quote:
    # v_sh600519="1~贵州茅台~600519~1780.01~..."
    if "=" not in body:
        raise ValueError("unexpected tencent quote response")
    payload = body.split("=", 1)[1].strip().strip(";").strip('"')
    parts = payload.split("~")
    if len(parts) < 50:
        raise ValueError(f"tencent quote fields too short: {len(parts)}")
    name = parts[1] or None
    last = float(parts[3] or 0)
    prev_close = float(parts[4] or 0) if parts[4] else None
    open_ = float(parts[5] or 0) if parts[5] else None
    volume = float(parts[6] or 0) if parts[6] else None
    bid = float(parts[9] or 0) if parts[9] else None
    ask = float(parts[19] or 0) if parts[19] else None
    high = float(parts[33] or 0) if parts[33] else None
    low = float(parts[34] or 0) if parts[34] else None
    change = float(parts[31] or 0) if parts[31] else None
    change_pct = float(parts[32] or 0) if parts[32] else None
    return Quote(
        symbol=sid.canonical,
        last=last,
        bid=bid,
        ask=ask,
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


def fetch_quote(sid: SymbolId, timeout: float = 8.0) -> Quote:
    if sid.prefix != "CN":
        raise ValueError("cn_watch only supports CN symbols")
    tcode = to_tencent_code(sid)
    url = QUOTE_URL.format(tencent_code=tcode)
    with httpx.Client(timeout=timeout, headers={"User-Agent": "data-facade/0.1"}) as client:
        r = client.get(url)
        r.raise_for_status()
        # Tencent may return gbk
        text = r.content.decode("gbk", errors="replace")
    return _parse_quote_body(text, sid)


def _interval_to_period(interval: str) -> str:
    mapping = {
        "1d": "day",
        "day": "day",
        "1w": "week",
        "week": "week",
        "1M": "month",
        "month": "month",
        "1m": "m1",
        "5m": "m5",
        "15m": "m15",
        "30m": "m30",
        "60m": "m60",
        "1h": "m60",
    }
    key = interval.strip()
    if key not in mapping:
        raise ValueError(f"unsupported interval '{interval}' for tencent kline")
    return mapping[key]


def fetch_bars(sid: SymbolId, interval: str = "1d", limit: int = 5, timeout: float = 10.0) -> list[Bar]:
    if sid.prefix != "CN":
        raise ValueError("cn_watch only supports CN symbols")
    tcode = to_tencent_code(sid)
    period = _interval_to_period(interval)
    limit = max(1, min(limit, 320))
    url = KLINE_URL.format(tencent_code=tcode, period=period, limit=limit)
    with httpx.Client(timeout=timeout, headers={"User-Agent": "data-facade/0.1"}) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
    # Structure: data.{tcode}.qfqday | day | ...
    node = (data.get("data") or {}).get(tcode) or {}
    series: Optional[list] = None
    for key in (f"qfq{period}", period, f"qfqday", "day"):
        if key in node and isinstance(node[key], list):
            series = node[key]
            break
    if not series:
        # try first list value
        for v in node.values():
            if isinstance(v, list) and v and isinstance(v[0], (list, tuple)):
                series = v
                break
    if not series:
        log.warning("no kline series for %s: keys=%s", tcode, list(node.keys()))
        return []
    bars: list[Bar] = []
    as_of = utc_now_iso()
    for row in series[-limit:]:
        # [date, open, close, high, low, volume, ...]
        if not row or len(row) < 5:
            continue
        open_time = str(row[0])
        if "T" not in open_time and len(open_time) == 10:
            open_time = f"{open_time}T00:00:00Z"
        bars.append(
            Bar(
                symbol=sid.canonical,
                interval=interval,
                open_time=open_time,
                open=float(row[1]),
                close=float(row[2]),
                high=float(row[3]),
                low=float(row[4]),
                volume=float(row[5]) if len(row) > 5 and row[5] not in (None, "") else None,
                as_of=as_of,
                source=SOURCE,
                stale=False,
            )
        )
    return bars
