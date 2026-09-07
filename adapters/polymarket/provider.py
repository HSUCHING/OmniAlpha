"""Polymarket PredictionProvider — Gamma via public_api; not equity Quote/Bar."""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from adapters.polymarket import public_api
from contracts.schema import utc_now_iso

log = logging.getLogger(__name__)
SOURCE = "polymarket-gamma"


def _parse_json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _f(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _normalize_outcomes(raw: dict[str, Any]) -> list[dict[str, Any]]:
    names = _parse_json_list(raw.get("outcomes_raw") or raw.get("outcomes"))
    prices = _parse_json_list(raw.get("outcome_prices") or raw.get("outcomePrices"))
    n = max(len(names), len(prices))
    out: list[dict[str, Any]] = []
    for i in range(n):
        name = str(names[i]) if i < len(names) else f"Outcome{i}"
        price = _f(prices[i]) if i < len(prices) else None
        if price is None:
            continue
        if price > 1.0:
            price = price / 100.0
        # clamp for model ge/le
        price = max(0.0, min(1.0, float(price)))
        out.append({"name": name, "price": price})
    return out


def _to_float(v: Any) -> Optional[float]:
    return _f(v)


def normalize_market(raw: dict[str, Any]) -> dict[str, Any]:
    """Map public_api / Gamma dict → PredictionMarket-compatible dict."""
    mid = str(raw.get("id") or "")
    outcomes = _normalize_outcomes(raw)
    return {
        "id": mid,
        "symbol": raw.get("symbol") or (f"POLY:{mid}" if mid else ""),
        "question": raw.get("question"),
        "slug": raw.get("slug"),
        "active": raw.get("active"),
        "closed": raw.get("closed"),
        "outcomes": outcomes,
        "volume": _to_float(raw.get("volume")),
        "liquidity": _to_float(raw.get("liquidity")),
        "end_date": raw.get("end_date"),
        "as_of": raw.get("as_of") or utc_now_iso(),
        "source": raw.get("source") or SOURCE,
        "stale": bool(raw.get("stale", False)),
    }


def market_to_quote(market: dict[str, Any]) -> dict[str, Any]:
    outcomes = market.get("outcomes") or []
    yes_price = no_price = None
    for o in outcomes:
        n = str(o.get("name") or "").strip().lower()
        p = _f(o.get("price"))
        if n in ("yes", "y") and p is not None:
            yes_price = p
        elif n in ("no", "n") and p is not None:
            no_price = p
    if yes_price is None and outcomes:
        yes_price = _f(outcomes[0].get("price"))
    if no_price is None and len(outcomes) > 1:
        no_price = _f(outcomes[1].get("price"))
    mid = str(market.get("id") or "")
    return {
        "market_id": mid,
        "symbol": market.get("symbol") or (f"POLY:{mid}" if mid else ""),
        "question": market.get("question"),
        "outcomes": outcomes,
        "yes_price": yes_price,
        "no_price": no_price,
        "as_of": market.get("as_of") or utc_now_iso(),
        "source": market.get("source") or SOURCE,
        "stale": bool(market.get("stale", False)),
    }


class PolymarketPredictionProvider:
    """Domain PredictionProvider protocol implementation."""

    def list_markets(self, limit: int = 20, q: Optional[str] = None) -> list[dict[str, Any]]:
        items = public_api.list_markets(limit=limit, q=q) or []
        return [normalize_market(m) for m in items if isinstance(m, dict)]

    def get_market(self, market_id: str) -> Optional[dict[str, Any]]:
        raw = public_api.get_market(market_id)
        if not raw:
            return None
        return normalize_market(raw)

    def get_quote(self, market_id: str) -> Optional[dict[str, Any]]:
        market = self.get_market(market_id)
        if not market:
            return None
        return market_to_quote(market)
