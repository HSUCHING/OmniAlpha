"""Shared market-adapter protocol. Vendor SDKs/URLs stay in adapter packages only."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from contracts.schema import Bar, Quote, SymbolId


@runtime_checkable
class MarketAdapter(Protocol):
    """Quote + bars for one market prefix (CN|US|CRYPTO|POLY)."""

    market: str

    def fetch_quote(self, sid: SymbolId) -> Quote: ...

    def fetch_bars(self, sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]: ...
