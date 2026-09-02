"""Prediction domain — calls registered provider only (no adapter imports)."""
from __future__ import annotations

import json
from typing import Any, Optional

from domain.prediction.ports import get_prediction_provider


def list_markets(limit: int = 20, q: Optional[str] = None) -> dict[str, Any]:
    provider = get_prediction_provider()
    if provider is None:
        return {
            "items": [],
            "total": 0,
            "warnings": ["prediction provider not registered"],
            "implemented": False,
        }
    items = provider.list_markets(limit=limit, q=q)
    return {"items": items, "total": len(items), "warnings": [], "implemented": True}


def list_events(limit: int = 10, active: bool = True) -> dict[str, Any]:
    _ = active
    return list_markets(limit=limit)


def get_market(market_id: str) -> dict[str, Any]:
    provider = get_prediction_provider()
    if provider is None:
        return {
            "item": None,
            "warnings": ["prediction provider not registered"],
            "implemented": False,
        }
    item = provider.get_market(market_id)
    if item is None:
        raise LookupError(f"market '{market_id}' not found")
    return {"item": item, "warnings": [], "implemented": True}


def get_quote(market_id: str) -> dict[str, Any]:
    result = get_market(market_id)
    item = result.get("item") or {}
    prices = item.get("outcome_prices")
    if isinstance(prices, str):
        try:
            prices = json.loads(prices)
        except json.JSONDecodeError:
            prices = None
    last = None
    if isinstance(prices, list) and prices:
        try:
            last = float(prices[0])
            if last > 1.0:
                last = last / 100.0
        except (TypeError, ValueError):
            last = None
    return {
        "market_id": item.get("id") or market_id,
        "symbol": item.get("symbol") or f"POLY:{market_id}",
        "question": item.get("question"),
        "last": last,
        "outcome_prices": prices,
        "as_of": item.get("as_of"),
        "source": item.get("source") or "polymarket",
        "stale": False,
        "implemented": True,
        "notes": "last is first-outcome probability in [0,1] when available",
    }


def get_predictions(*_args, **_kwargs):
    return list_markets(limit=20)
