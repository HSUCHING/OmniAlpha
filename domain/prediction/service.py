"""Prediction domain — registered provider only."""
from __future__ import annotations

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
    items = provider.list_markets(limit=limit, q=q) or []
    return {"items": items, "total": len(items), "warnings": [], "implemented": True}


def list_events(limit: int = 10, active: bool = True, q: Optional[str] = None) -> dict[str, Any]:
    """Thin alias of list_markets (events ≈ markets in phase-1)."""
    _ = active
    out = list_markets(limit=limit, q=q)
    out["active_filter"] = active
    return out


def get_market(market_id: str) -> dict[str, Any]:
    mid = (market_id or "").strip()
    if not mid:
        raise ValueError("empty market_id")
    provider = get_prediction_provider()
    if provider is None:
        raise LookupError("prediction provider not registered")
    item = provider.get_market(mid)
    if not item:
        raise LookupError(f"prediction market '{mid}' not found")
    return item


def get_quote(market_id: str) -> dict[str, Any]:
    mid = (market_id or "").strip()
    if not mid:
        raise ValueError("empty market_id")
    provider = get_prediction_provider()
    if provider is None:
        raise LookupError("prediction provider not registered")
    # Prefer provider helper when available
    get_q = getattr(provider, "get_quote", None)
    if callable(get_q):
        quote = get_q(mid)
        if not quote:
            raise LookupError(f"prediction market '{mid}' not found")
        return quote
    item = provider.get_market(mid)
    if not item:
        raise LookupError(f"prediction market '{mid}' not found")
    outcomes = item.get("outcomes") or []
    yes_price = no_price = None
    for o in outcomes:
        n = str(o.get("name") or "").strip().lower()
        try:
            p = float(o.get("price"))
        except (TypeError, ValueError):
            continue
        if n in ("yes", "y"):
            yes_price = p
        elif n in ("no", "n"):
            no_price = p
    if yes_price is None and outcomes:
        try:
            yes_price = float(outcomes[0].get("price"))
        except (TypeError, ValueError, IndexError):
            yes_price = None
    if no_price is None and len(outcomes) > 1:
        try:
            no_price = float(outcomes[1].get("price"))
        except (TypeError, ValueError, IndexError):
            no_price = None
    return {
        "market_id": item.get("id") or mid,
        "symbol": item.get("symbol") or f"POLY:{mid}",
        "question": item.get("question"),
        "outcomes": outcomes,
        "yes_price": yes_price,
        "no_price": no_price,
        "as_of": item.get("as_of"),
        "source": item.get("source", "polymarket-gamma"),
        "stale": bool(item.get("stale", False)),
    }
