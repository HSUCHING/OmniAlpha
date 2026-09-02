"""Market data: quotes (Redis + domain ports) and bars. No vendor URLs / adapter imports."""
from __future__ import annotations

import json
import logging
from typing import Optional

from contracts.schema import Bar, BarList, Quote, QuoteList, SymbolId, utc_now_iso
from domain.marketdata.ports import get_provider
from domain.redis_client import get_redis

log = logging.getLogger(__name__)

QUOTE_TTL = 30
QUOTE_KEY = "quote:{symbol}"


def _cache_get(symbol: str) -> Optional[Quote]:
    try:
        raw = get_redis().get(QUOTE_KEY.format(symbol=symbol))
        if not raw:
            return None
        data = json.loads(raw)
        data["stale"] = False
        return Quote.model_validate(data)
    except Exception as e:
        log.warning("redis get failed: %s", e)
        return None


def _cache_set(quote: Quote) -> None:
    try:
        get_redis().setex(
            QUOTE_KEY.format(symbol=quote.symbol),
            QUOTE_TTL,
            quote.model_dump_json(),
        )
    except Exception as e:
        log.warning("redis set failed: %s", e)


def _refresh(sid: SymbolId) -> Quote:
    adapter = get_provider(sid.prefix)
    if adapter is None:
        raise LookupError(f"market '{sid.prefix}' quote adapter not registered")
    q = adapter.fetch_quote(sid)
    _cache_set(q)
    return q


def get_quotes(symbols: list[SymbolId]) -> QuoteList:
    items: list[Quote] = []
    warnings: list[str] = []
    for sid in symbols:
        cached = _cache_get(sid.canonical)
        if cached:
            items.append(cached)
            continue
        adapter = get_provider(sid.prefix)
        if adapter is None:
            warnings.append(
                f"{sid.canonical}: market '{sid.prefix}' quote adapter not registered"
            )
            continue
        try:
            items.append(_refresh(sid))
        except Exception as e:
            log.exception("quote refresh failed for %s", sid.canonical)
            warnings.append(f"{sid.canonical}: refresh failed: {e}")
    return QuoteList(items=items, warnings=warnings)


def get_bars(sid: SymbolId, interval: str = "1d", limit: int = 5) -> BarList:
    limit = max(1, min(limit, 500))
    warnings: list[str] = []
    adapter = get_provider(sid.prefix)
    if adapter is None:
        warnings.append(f"{sid.canonical}: market '{sid.prefix}' bars adapter not registered")
        return BarList(items=[], warnings=warnings)

    try:
        bars = adapter.fetch_bars(sid, interval=interval, limit=limit)
        if bars:
            return BarList(items=bars, warnings=warnings)
        warnings.append(f"{sid.canonical}: kline empty; trying synthetic from last quote")
    except Exception as e:
        log.exception("bars fetch failed for %s", sid.canonical)
        warnings.append(f"{sid.canonical}: kline failed: {e}; trying synthetic")

    ql = get_quotes([sid])
    if ql.items:
        q = ql.items[0]
        bar = Bar(
            symbol=sid.canonical,
            interval=interval,
            open_time=q.as_of,
            open=q.open or q.last,
            high=q.high or q.last,
            low=q.low or q.last,
            close=q.last,
            volume=q.volume,
            as_of=utc_now_iso(),
            source="synthetic:last_quote",
            stale=True,
        )
        warnings.append("bars are synthetic from last quote")
        return BarList(items=[bar], warnings=warnings)
    warnings.extend(ql.warnings)
    warnings.append("no quote available for synthetic bars")
    return BarList(items=[], warnings=warnings)
