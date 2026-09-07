"""FastMCP tools mirroring /v1 semantics (phase-1)."""
from __future__ import annotations

from typing import Optional

from domain.id import parse_symbol, parse_symbols
from domain.marketdata import get_bars, get_quotes
from domain.meta import get_capabilities_matrix
from domain import prediction as prediction_svc
from domain.reference import search_instruments as ref_search


def register_tools(mcp) -> None:
    @mcp.tool(name="search_instruments")
    def search_instruments(q: str, market: Optional[str] = None, limit: int = 20) -> dict:
        """Search instruments by text query and optional market prefix (CN, US, CRYPTO, POLY)."""
        result = ref_search(q=q, market=market, limit=limit)
        return result.model_dump()

    @mcp.tool(name="get_quotes")
    def get_quotes_tool(symbols: str) -> dict:
        """Get quotes for comma-separated canonical symbols e.g. CN:600519,US:AAPL. Not for POLY prediction."""
        sids = parse_symbols(symbols)
        result = get_quotes(sids)
        return result.model_dump()

    @mcp.tool(name="get_bars")
    def get_bars_tool(symbol: str, interval: str = "1d", limit: int = 5) -> dict:
        """Get OHLCV bars for a canonical symbol e.g. CN:600519. Not for POLY prediction."""
        sid = parse_symbol(symbol)
        result = get_bars(sid, interval=interval, limit=limit)
        return result.model_dump()

    @mcp.tool(name="get_capabilities")
    def get_capabilities() -> dict:
        """Return market × capability matrix (implemented|partial|unsupported)."""
        return get_capabilities_matrix()

    @mcp.tool(name="search_prediction_markets")
    def search_prediction_markets(q: Optional[str] = None, limit: int = 20) -> dict:
        """Search Polymarket prediction markets (PredictionMarketList). Not equity Quote/Bar."""
        from contracts.schema import PredictionMarket, PredictionMarketList

        raw = prediction_svc.list_markets(limit=limit, q=q)
        return PredictionMarketList(
            items=[PredictionMarket.model_validate(x) for x in (raw.get("items") or [])],
            total=int(raw.get("total") or 0),
            warnings=list(raw.get("warnings") or []),
        ).model_dump()

    @mcp.tool(name="get_prediction_market")
    def get_prediction_market(market_id: str) -> dict:
        """Get a prediction market by id or POLY:{id} (PredictionMarket)."""
        from contracts.schema import PredictionMarket

        mid = (market_id or "").strip()
        if not mid:
            return {"error": {"code": "invalid_id", "message": "empty market_id"}}
        try:
            item = prediction_svc.get_market(mid)
        except ValueError as e:
            return {"error": {"code": "invalid_id", "message": str(e)}}
        except LookupError as e:
            return {"error": {"code": "not_found", "message": str(e)}}
        return PredictionMarket.model_validate(item).model_dump()

    @mcp.tool(name="get_prediction_quote")
    def get_prediction_quote(market_id: str) -> dict:
        """Get prediction probabilities for a market (PredictionQuote). Use /v1/prediction/quote, not /v1/quotes."""
        from contracts.schema import PredictionQuote

        mid = (market_id or "").strip()
        if not mid:
            return {"error": {"code": "invalid_id", "message": "empty market_id"}}
        try:
            quote = prediction_svc.get_quote(mid)
        except ValueError as e:
            return {"error": {"code": "invalid_id", "message": str(e)}}
        except LookupError as e:
            return {"error": {"code": "not_found", "message": str(e)}}
        return PredictionQuote.model_validate(quote).model_dump()
