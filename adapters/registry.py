"""Adapter registry: domain resolves market prefix -> MarketAdapter (no vendor URLs)."""
from __future__ import annotations

import logging
from typing import Optional

from adapters.base import MarketAdapter

log = logging.getLogger(__name__)

_ADAPTERS: dict[str, MarketAdapter] = {}
_WIRED = False


def register_adapter(prefix: str, adapter: MarketAdapter) -> None:
    _ADAPTERS[prefix.upper()] = adapter


def get_adapter(prefix: str) -> Optional[MarketAdapter]:
    """Return registered adapter for CN|US|CRYPTO|POLY, or None."""
    ensure_registered()
    return _ADAPTERS.get(prefix.upper())


def supported_markets() -> list[str]:
    ensure_registered()
    return sorted(_ADAPTERS.keys())


def capabilities() -> dict[str, dict[str, bool]]:
    ensure_registered()
    return {
        "CN": {"instruments": True, "quotes": True, "bars": True, "analyze": False, "screen": False, "prediction": False},
        "US": {"instruments": True, "quotes": True, "bars": True, "analyze": False, "screen": False, "prediction": False},
        "CRYPTO": {"instruments": True, "quotes": True, "bars": True, "analyze": False, "screen": False, "prediction": False},
        "POLY": {"instruments": True, "quotes": True, "bars": False, "analyze": False, "screen": False, "prediction": False},
    }


def ensure_registered() -> None:
    global _WIRED
    if _WIRED:
        return
    from adapters.cn_watch import CnTencentAdapter
    from adapters.crypto import OkxCryptoAdapter
    from adapters.polymarket import PolymarketAdapter
    from adapters.us import UsYfinanceAdapter

    register_adapter("CN", CnTencentAdapter())
    register_adapter("US", UsYfinanceAdapter())
    register_adapter("CRYPTO", OkxCryptoAdapter())
    register_adapter("POLY", PolymarketAdapter())

    # Mirror into domain ports for wiring/legacy callers
    try:
        from domain.marketdata.ports import register_provider

        for prefix, adapter in list(_ADAPTERS.items()):
            register_provider(prefix, adapter)
    except Exception as e:
        log.warning("could not mirror adapters into domain ports: %s", e)

    try:
        from domain.prediction.ports import register_prediction_provider

        class _PolyPredictionProvider:
            def list_markets(self, limit: int = 20, q=None):
                from adapters.polymarket import list_markets

                return list_markets(limit=limit, q=q)

            def get_market(self, market_id: str):
                from adapters.polymarket import get_market

                return get_market(market_id)

        register_prediction_provider(_PolyPredictionProvider())
    except Exception as e:
        log.warning("prediction provider not registered: %s", e)

    _WIRED = True
    log.info("adapters registered: %s", ", ".join(sorted(_ADAPTERS.keys())))


def setup_providers() -> None:
    """Facade / wiring lifespan hook."""
    ensure_registered()
