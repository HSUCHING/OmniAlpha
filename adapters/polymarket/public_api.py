"""Minimal Polymarket public Gamma API (prediction markets)."""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from contracts.schema import utc_now_iso

log = logging.getLogger(__name__)
SOURCE = "polymarket-gamma"
GAMMA_BASE = "https://gamma-api.polymarket.com"


def list_markets(limit: int = 20, q: Optional[str] = None, timeout: float = 12.0) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 100))
    params: dict[str, Any] = {"limit": limit, "active": "true", "closed": "false"}
    if q:
        # Gamma supports text search via /public-search in newer APIs; fall back to filter client-side
        params["limit"] = min(limit * 3, 100)
    url = f"{GAMMA_BASE}/markets"
    with httpx.Client(timeout=timeout, headers={"User-Agent": "omnialpha/0.1"}) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    if not isinstance(data, list):
        data = data.get("data") or data.get("markets") or []
    items: list[dict[str, Any]] = []
    as_of = utc_now_iso()
    needle = (q or "").strip().lower()
    for m in data:
        if not isinstance(m, dict):
            continue
        question = str(m.get("question") or m.get("title") or "")
        mid = str(m.get("id") or m.get("conditionId") or m.get("slug") or "")
        if needle and needle not in question.lower() and needle not in mid.lower():
            continue
        items.append(
            {
                "id": mid,
                "symbol": f"POLY:{mid}" if mid else None,
                "question": question,
                "slug": m.get("slug"),
                "active": m.get("active"),
                "closed": m.get("closed"),
                "outcome_prices": m.get("outcomePrices") or m.get("outcome_prices"),
                "outcomes_raw": m.get("outcomes"),
                "volume": m.get("volume") or m.get("volumeNum"),
                "liquidity": m.get("liquidity") or m.get("liquidityNum"),
                "end_date": m.get("endDate") or m.get("end_date_iso"),
                "as_of": as_of,
                "source": SOURCE,
                "stale": False,
            }
        )
        if len(items) >= limit:
            break
    return items


def get_market(market_id: str, timeout: float = 12.0) -> Optional[dict[str, Any]]:
    mid = market_id.strip()
    if mid.upper().startswith("POLY:"):
        mid = mid.split(":", 1)[1]
    url = f"{GAMMA_BASE}/markets/{mid}"
    with httpx.Client(timeout=timeout, headers={"User-Agent": "omnialpha/0.1"}) as client:
        r = client.get(url)
        if r.status_code in (404, 422):
            # try slug / id search via list
            found = list_markets(limit=50, q=mid)
            for item in found:
                if item.get("id") == mid or item.get("slug") == mid:
                    return item
            return None
        r.raise_for_status()
        m = r.json()
    if isinstance(m, list):
        m = m[0] if m else None
    if not isinstance(m, dict):
        return None
    as_of = utc_now_iso()
    return {
        "id": str(m.get("id") or mid),
        "symbol": f"POLY:{m.get('id') or mid}",
        "question": m.get("question") or m.get("title"),
        "slug": m.get("slug"),
        "active": m.get("active"),
        "closed": m.get("closed"),
        "outcome_prices": m.get("outcomePrices") or m.get("outcome_prices"),
        "outcomes_raw": m.get("outcomes"),
        "volume": m.get("volume") or m.get("volumeNum"),
        "liquidity": m.get("liquidity") or m.get("liquidityNum"),
        "end_date": m.get("endDate") or m.get("end_date_iso"),
        "as_of": as_of,
        "source": SOURCE,
        "stale": False,
        "raw_keys": sorted(m.keys())[:40],
    }
