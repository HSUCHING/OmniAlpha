"""FastMCP tools mirroring /v1 semantics (phase-1)."""
from __future__ import annotations

from typing import Optional

from domain.id import parse_symbol, parse_symbols
from domain.marketdata import get_bars, get_quotes
from domain.meta import get_capabilities_matrix
from domain.reference import search_instruments as ref_search


def register_tools(mcp) -> None:
    @mcp.tool(name="search_instruments")
    def search_instruments(q: str, market: Optional[str] = None, limit: int = 20) -> dict:
        """Search instruments by text query and optional market prefix (CN, US, CRYPTO, POLY)."""
        result = ref_search(q=q, market=market, limit=limit)
        return result.model_dump()

    @mcp.tool(name="get_quotes")
    def get_quotes_tool(symbols: str) -> dict:
        """Get quotes for comma-separated canonical symbols e.g. CN:600519,US:AAPL."""
        sids = parse_symbols(symbols)
        result = get_quotes(sids)
        return result.model_dump()

    @mcp.tool(name="get_bars")
    def get_bars_tool(symbol: str, interval: str = "1d", limit: int = 5) -> dict:
        """Get OHLCV bars for a canonical symbol e.g. CN:600519."""
        sid = parse_symbol(symbol)
        result = get_bars(sid, interval=interval, limit=limit)
        return result.model_dump()

    @mcp.tool(name="get_capabilities")
    def get_capabilities() -> dict:
        """Return market × capability matrix (implemented|partial|unsupported)."""
        return get_capabilities_matrix()
