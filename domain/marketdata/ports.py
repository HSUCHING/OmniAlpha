"""Market-data ports: domain owns the interface; apps wires implementations."""
from __future__ import annotations
from typing import Optional, Protocol
from contracts.schema import Bar, Quote, SymbolId

class MarketDataProvider(Protocol):
    def fetch_quote(self, sid: SymbolId) -> Quote: ...
    def fetch_bars(self, sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]: ...

_PROVIDERS: dict[str, MarketDataProvider] = {}

def register_provider(prefix: str, provider: MarketDataProvider) -> None:
    _PROVIDERS[prefix.upper()] = provider

def get_provider(prefix: str) -> Optional[MarketDataProvider]:
    return _PROVIDERS.get(prefix.upper())

def list_registered_markets() -> list[str]:
    return sorted(_PROVIDERS.keys())

def clear_providers() -> None:
    _PROVIDERS.clear()
