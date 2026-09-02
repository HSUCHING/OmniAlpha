"""Domain marketdata ports — thin mirror of adapters.registry (preferred API: get_adapter)."""
from __future__ import annotations

from typing import Optional, Protocol

from contracts.schema import Bar, Quote, SymbolId


class MarketDataProvider(Protocol):
    def fetch_quote(self, sid: SymbolId) -> Quote: ...

    def fetch_bars(self, sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]: ...


def register_provider(prefix: str, provider: MarketDataProvider) -> None:
    from adapters.registry import register_adapter

    register_adapter(prefix, provider)  # type: ignore[arg-type]


def get_provider(prefix: str) -> Optional[MarketDataProvider]:
    from adapters.registry import get_adapter

    return get_adapter(prefix)


def list_registered_markets() -> list[str]:
    from adapters.registry import supported_markets

    return supported_markets()
