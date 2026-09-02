"""Prediction domain — registered provider only."""
from __future__ import annotations
from typing import Any, Optional
from domain.prediction.ports import get_prediction_provider

def list_markets(limit: int = 20, q: Optional[str] = None) -> dict[str, Any]:
    provider = get_prediction_provider()
    if provider is None:
        return {"items": [], "total": 0, "warnings": ["prediction provider not registered"], "implemented": False}
    items = provider.list_markets(limit=limit, q=q) or []
    return {"items": items, "total": len(items), "warnings": [], "implemented": True}

def list_events(limit: int = 10, active: bool = True) -> dict[str, Any]:
    out = list_markets(limit=limit)
    out["active_filter"] = active
    return out

def get_market(market_id: str) -> dict[str, Any]:
    provider = get_prediction_provider()
    if provider is None:
        return {"item": None, "warnings": ["prediction provider not registered"], "implemented": False}
    item = provider.get_market(market_id)
    warnings = [] if item else [f"market '{market_id}' not found"]
    return {"item": item, "warnings": warnings, "implemented": True}

def get_quote(market_id: str) -> dict[str, Any]:
    got = get_market(market_id)
    item = got.get("item")
    if not item:
        raise LookupError(f"prediction market '{market_id}' not found")
    return {"market_id": market_id, "source": item.get("source", "polymarket"), "stale": False, "market": item, "warnings": got.get("warnings") or []}
