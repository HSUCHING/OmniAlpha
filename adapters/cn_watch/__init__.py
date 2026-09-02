"""CN A-share watch adapter (Tencent)."""
from __future__ import annotations

from contracts.schema import Bar, Quote, SymbolId

from .tencent import fetch_bars, fetch_quote, to_tencent_code


class CnTencentAdapter:
    market = "CN"

    def fetch_quote(self, sid: SymbolId) -> Quote:
        return fetch_quote(sid)

    def fetch_bars(self, sid: SymbolId, interval: str = "1d", limit: int = 5) -> list[Bar]:
        return fetch_bars(sid, interval=interval, limit=limit)


__all__ = ["CnTencentAdapter", "fetch_bars", "fetch_quote", "to_tencent_code"]
