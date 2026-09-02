"""POLY adapter via Polymarket Gamma public API. Quote.last = outcome probability."""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

from contracts.schema import Bar, Quote, SymbolId, utc_now_iso

log = logging.getLogger(__name__)
SOURCE = "polymarket"
# last is probability in [0, 1] (documented via source=polymarket)
GAMMA_BASE = "https://gamma-api.polymarket.com"


def fetch_quote(sid: SymbolId, timeout: float = 10.0) -> Quote:
    if sid.prefix != "POLY":
        raise ValueError("polymarket adapter only supports POLY symbols")
    market_id = sid.code
    with httpx.Client(timeout=timeout, headers={"User-Agent": "data-facade/0.1"}) as client:
        market = _resolve_market(client, market_id)
    if not market:
        raise ValueError(f"polymarket market not found: {market_id}")

    last = _extract_probability(market)
    if last is None:
        raise ValueError(f"polymarket market has no outcome prices: {market_id}")

    name = market.get("question") or market.get("title") or market.get("slug")
    bid = ask = None
    # bestBid/bestAsk sometimes present on CLOB-enriched payloads
    bid = _f(market.get("bestBid"))
    ask = _f(market.get("bestAsk"))

    return Quote(
        symbol=sid.canonical,
        last=float(last),
        bid=bid,
        ask=ask,
        open=None,
        high=None,
        low=None,
        prev_close=None,
        volume=_f(market.get("volume") or market.get("volumeNum")),
        change=None,
        change_pct=None,
        name=str(name) if name else None,
        as_of=utc_now_iso(),
        source=SOURCE,
        stale=False,
    )


def fetch_bars(sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]:
    """Gamma does not expose OHLCV bars for prediction markets in phase-1."""
    if sid.prefix != "POLY":
        raise ValueError("polymarket adapter only supports POLY symbols")
    return []


def _resolve_market(client: httpx.Client, market_id: str) -> Optional[dict[str, Any]]:
    # Try by numeric/condition id first
    for path in (f"/markets/{market_id}",):
        try:
            r = client.get(f"{GAMMA_BASE}{path}")
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and data:
                    return data
                if isinstance(data, list) and data:
                    return data[0]
        except Exception as e:
            log.debug("gamma GET %s failed: %s", path, e)

    # slug or id query
    for params in (
        {"id": market_id},
        {"slug": market_id},
        {"condition_ids": market_id},
    ):
        try:
            r = client.get(f"{GAMMA_BASE}/markets", params=params)
            if r.status_code != 200:
                continue
            data = r.json()
            if isinstance(data, list) and data:
                return data[0]
            if isinstance(data, dict):
                if data.get("id") or data.get("question"):
                    return data
                items = data.get("markets") or data.get("data") or []
                if items:
                    return items[0]
        except Exception as e:
            log.debug("gamma markets query %s failed: %s", params, e)
    return None


def _extract_probability(market: dict[str, Any]) -> Optional[float]:
    """Prefer first outcome mid/last trade probability as float in [0, 1]."""
    prices = market.get("outcomePrices")
    if isinstance(prices, str):
        try:
            prices = json.loads(prices)
        except json.JSONDecodeError:
            prices = None
    if isinstance(prices, list) and prices:
        p = _f(prices[0])
        if p is not None:
            # if apparently 0-100 scale, normalize
            if p > 1.0:
                p = p / 100.0
            return p

    # lastTradePrice / last on market
    for key in ("lastTradePrice", "last", "probability", "yesPrice"):
        p = _f(market.get(key))
        if p is not None:
            if p > 1.0:
                p = p / 100.0
            return p

    tokens = market.get("tokens") or market.get("clobTokenIds")
    if isinstance(tokens, list) and tokens:
        t0 = tokens[0]
        if isinstance(t0, dict):
            p = _f(t0.get("price") or t0.get("lastPrice"))
            if p is not None:
                if p > 1.0:
                    p = p / 100.0
                return p
    return None


def _f(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class PolymarketAdapter:
    market = "POLY"

    def fetch_quote(self, sid: SymbolId) -> Quote:
        return fetch_quote(sid)

    def fetch_bars(self, sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]:
        return fetch_bars(sid, interval=interval, limit=limit)
