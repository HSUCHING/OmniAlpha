"""Data Facade — FastAPI /v1 + FastMCP /mcp."""
from __future__ import annotations

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from contracts.schema import (
    BarList,
    HealthResponse,
    InstrumentList,
    QuoteList,
)
from domain import db
from domain.id import parse_symbol, parse_symbols
from domain.marketdata import get_bars, get_quotes
from domain.reference import list_instruments, search_instruments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("facade")

API_KEY = os.getenv("DATA_FACADE_API_KEY", "").strip()
FASTMCP_AVAILABLE = False
mcp_app = None
_combine_lifespans = None

try:
    from fastmcp import FastMCP
    from apps.facade.mcp_tools import register_tools

    mcp = FastMCP("data-facade")
    register_tools(mcp)
    mcp_app = mcp.http_app(path="/")
    FASTMCP_AVAILABLE = True
    try:
        from fastmcp.utilities.lifespan import combine_lifespans as _combine_lifespans
    except ImportError:
        try:
            from fastmcp.server.lifespan import combine_lifespans as _combine_lifespans
        except ImportError:
            _combine_lifespans = None
    log.info("FastMCP enabled")
except Exception as e:
    log.warning("FastMCP not available (%s); /mcp will be a health stub", e)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    log.info("initializing database...")
    # retry a few times for compose race
    last_err = None
    for i in range(15):
        try:
            db.init_db()
            last_err = None
            break
        except Exception as err:
            last_err = err
            log.warning("db init attempt %s failed: %s", i + 1, err)
            time.sleep(1)
    if last_err:
        raise last_err
    log.info("database ready")
    yield


def _build_lifespan():
    if mcp_app is not None and getattr(mcp_app, "lifespan", None) is not None:
        if _combine_lifespans is not None:
            return _combine_lifespans(app_lifespan, mcp_app.lifespan)

        @asynccontextmanager
        async def combined(app: FastAPI):
            async with app_lifespan(app):
                async with mcp_app.lifespan(app):
                    yield

        return combined
    return app_lifespan


app = FastAPI(
    title="Data Facade",
    version="0.1.0",
    description="L0–L5 finance data product skeleton (phase-1)",
    lifespan=_build_lifespan(),
)


async def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    if not API_KEY:
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    started = time.time()
    response: Response = await call_next(request)
    market = request.query_params.get("market") or request.query_params.get("symbols") or ""
    if not market:
        market = request.query_params.get("symbol") or ""
    entry = {
        "msg": "access",
        "method": request.method,
        "path": request.url.path,
        "market": market,
        "status": response.status_code,
        "latency_ms": round((time.time() - started) * 1000, 2),
    }
    log.info(json.dumps(entry, ensure_ascii=False))
    return response


@app.get("/healthz", response_model=HealthResponse, tags=["ops"])
def healthz():
    return HealthResponse(status="ok")


@app.get("/v1/instruments", response_model=InstrumentList, tags=["reference"], dependencies=[Depends(require_api_key)])
def v1_instruments(
    market: Optional[str] = Query(None, description="Market prefix filter: CN, US, CRYPTO, POLY"),
    q: Optional[str] = Query(None, description="Search text"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return list_instruments(market=market, q=q, limit=limit, offset=offset)


@app.get("/v1/instruments/search", response_model=InstrumentList, tags=["reference"], dependencies=[Depends(require_api_key)])
def v1_instruments_search(
    q: str = Query(..., min_length=1),
    market: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    return search_instruments(q=q, market=market, limit=limit)


@app.get("/v1/quotes", response_model=QuoteList, tags=["marketdata"], dependencies=[Depends(require_api_key)])
def v1_quotes(
    symbols: str = Query(..., description="Comma-separated canonical ids e.g. CN:600519,US:AAPL"),
):
    sids = parse_symbols(symbols)
    return get_quotes(sids)


@app.get("/v1/bars", response_model=BarList, tags=["marketdata"], dependencies=[Depends(require_api_key)])
def v1_bars(
    symbol: str = Query(..., description="Canonical id e.g. CN:600519"),
    interval: str = Query("1d", description="Bar interval e.g. 1d, 1h, 5m"),
    limit: int = Query(5, ge=1, le=500),
):
    sid = parse_symbol(symbol)
    return get_bars(sid, interval=interval, limit=limit)


if mcp_app is not None:
    app.mount("/mcp", mcp_app)
else:

    @app.get("/mcp", tags=["mcp"])
    @app.get("/mcp/health", tags=["mcp"])
    def mcp_stub():
        return JSONResponse(
            {
                "status": "stub",
                "detail": "fastmcp not installed; install fastmcp for real MCP tools",
                "tools": ["search_instruments", "get_quotes", "get_bars"],
            }
        )
