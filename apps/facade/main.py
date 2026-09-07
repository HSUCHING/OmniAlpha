"""OmniAlpha Facade — FastAPI /v1 + FastMCP /mcp."""
from __future__ import annotations

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.facade.wiring import setup_providers
from contracts.schema import (
    ApiError,
    BarList,
    CapabilitiesResponse,
    CapabilityFlags,
    HealthResponse,
    InstrumentList,
    PredictionMarket,
    PredictionMarketList,
    PredictionQuote,
    QuoteList,
    ReadyResponse,
)
from domain import db
from domain.health import check_ready
from domain.id import parse_symbol, parse_symbols
from domain.marketdata import get_bars, get_quotes
from domain.meta import get_capabilities_matrix
from domain import prediction as prediction_svc
from domain.reference import list_instruments, search_instruments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("omnialpha")

API_KEY = os.getenv("DATA_FACADE_API_KEY", "").strip()
FASTMCP_AVAILABLE = False
mcp_app = None
_combine_lifespans = None

try:
    from fastmcp import FastMCP
    from apps.facade.mcp_tools import register_tools

    mcp = FastMCP("omnialpha")
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
    setup_providers()
    log.info("initializing database...")
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
    title="OmniAlpha",
    version="0.1.0",
    description="Unified multi-market data facade (CN/US/CRYPTO/POLY)",
    lifespan=_build_lifespan(),
)

# CORS for public Scalar apidoc only — exact origins, no wildcard reflection.
# Authenticated requests still require X-API-Key; OPTIONS has no business body.
_CORS_ORIGINS = [
    "https://apidoc.metacognix.xyz",
    "http://127.0.0.1:8701",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type", "Accept"],
)


# ApiError codes locked to contract five: not_found|unsupported|stale|invalid_id|rate_limited
_ID_HINTS = ("symbol", "prefix", "PREFIX:CODE", "market prefix", "empty code", "at least one symbol")


def _api_error(code: str, message: str, *, market=None, capability=None) -> dict:
    return ApiError(code=code, message=message, market=market, capability=capability).model_dump()


def _looks_like_invalid_id(detail) -> bool:
    text = detail if isinstance(detail, str) else str(detail or "")
    lower = text.lower()
    return any(h.lower() in lower for h in _ID_HINTS)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    message = detail if isinstance(detail, str) else (str(detail) if detail is not None else "error")
    headers = getattr(exc, "headers", None)
    if exc.status_code == 401:
        return JSONResponse(status_code=401, content={"detail": message}, headers=headers)
    if exc.status_code == 404:
        return JSONResponse(status_code=404, content=_api_error("not_found", message), headers=headers)
    if exc.status_code == 501:
        return JSONResponse(status_code=501, content=_api_error("unsupported", message), headers=headers)
    if exc.status_code == 422 and _looks_like_invalid_id(detail):
        return JSONResponse(status_code=422, content=_api_error("invalid_id", message), headers=headers)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=headers)


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
    return HealthResponse(status="ok", service="omnialpha", version="0.1.0")


@app.get("/health/ready", response_model=ReadyResponse, tags=["ops"])
def health_ready():
    raw = check_ready()
    ok = bool(raw.get("postgres")) and bool(raw.get("redis"))
    failed = raw.get("failed") or []
    details = raw.get("details") or {}
    detail = "; ".join(f"{k}: {details[k]}" for k in failed if k in details) or None
    body = ReadyResponse(
        status="ok" if ok else "degraded",
        postgres=bool(raw.get("postgres")),
        redis=bool(raw.get("redis")),
        service="omnialpha",
        detail=detail,
    )
    if not ok:
        return JSONResponse(status_code=503, content=body.model_dump())
    return body


def _capabilities() -> CapabilitiesResponse:
    """Build API response from truthful domain matrix (POLY watch/query via Polymarket)."""
    m = get_capabilities_matrix()
    markets: dict[str, CapabilityFlags] = {}
    provider_by_market = {
        "CN": "tencent",
        "US": "yfinance",
        "CRYPTO": "okx",
        "POLY": "polymarket-gamma",
    }
    notes_by_market = {
        "CN": "A-share quotes/bars via Tencent",
        "US": "US equities quotes/bars via Yahoo Finance",
        "CRYPTO": "Spot quotes/bars via OKX public REST (httpx)",
        "POLY": "Polymarket venue watch/query via /v1/prediction/* (Gamma); prediction=model forecasts TBD",
    }
    for mkt, caps in m["matrix"].items():
        watch = caps["watch"]["status"] == "implemented"
        query = caps["query"]["status"] == "implemented"
        prediction = caps.get("prediction", {}).get("status") == "implemented"
        # Prefer market-specific provider when any capability is live
        live = watch or query or prediction
        markets[mkt] = CapabilityFlags(
            watch=watch,
            query=query,
            analyze=False,
            screen=False,
            prediction=prediction,
            provider=provider_by_market.get(mkt) if live else None,
            notes=notes_by_market.get(mkt),
        )
    matrix = []
    for mkt, flags in markets.items():
        for cap in ("watch", "query", "analyze", "screen", "prediction"):
            implemented = bool(getattr(flags, cap))
            prov = None
            if implemented:
                if cap == "prediction" and mkt == "POLY":
                    prov = "polymarket-gamma"
                else:
                    prov = flags.provider
            matrix.append(
                {
                    "market": mkt,
                    "capability": cap,
                    "implemented": implemented,
                    "provider": prov,
                }
            )
    return CapabilitiesResponse(phase="phase1", markets=markets, matrix=matrix)


@app.get("/v1/meta/capabilities", response_model=CapabilitiesResponse, tags=["meta"])
def v1_meta_capabilities():
    return _capabilities()


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


def _phase1_not_implemented(capability: str, detail: str):
    return JSONResponse(
        status_code=501,
        content=_api_error("unsupported", detail, capability=capability),
    )


@app.get("/v1/analyze", tags=["analytics"], dependencies=[Depends(require_api_key)])
def v1_analyze():
    return _phase1_not_implemented("analyze", "analyze not implemented in phase-1")


@app.get("/v1/analytics/indicators", tags=["analytics"], dependencies=[Depends(require_api_key)])
def v1_analytics_indicators():
    return _phase1_not_implemented("analyze", "analytics not implemented in phase-1")


@app.get("/v1/screen", tags=["screener"], dependencies=[Depends(require_api_key)])
def v1_screen():
    return _phase1_not_implemented("screen", "screen not implemented in phase-1")


@app.get("/v1/screener/run", tags=["screener"], dependencies=[Depends(require_api_key)])
def v1_screener_run(market: Optional[str] = Query(None)):
    _ = market
    return _phase1_not_implemented("screen", "screener not implemented in phase-1")


def _prediction_invalid_id(message: str):
    return JSONResponse(
        status_code=422,
        content=_api_error("invalid_id", message, market="POLY", capability="prediction"),
    )


def _prediction_not_found(message: str):
    return JSONResponse(
        status_code=404,
        content=_api_error("not_found", message, market="POLY", capability="prediction"),
    )


@app.get(
    "/v1/prediction/events",
    response_model=PredictionMarketList,
    tags=["prediction"],
    dependencies=[Depends(require_api_key)],
)
def v1_prediction_events(
    limit: int = Query(10, ge=1, le=100),
    q: Optional[str] = Query(None, description="Filter by question/id substring"),
    active: bool = Query(True),
):
    raw = prediction_svc.list_events(limit=limit, active=active, q=q)
    return PredictionMarketList(
        items=[PredictionMarket.model_validate(x) for x in (raw.get("items") or [])],
        total=int(raw.get("total") or 0),
        warnings=list(raw.get("warnings") or []),
    )


@app.get(
    "/v1/prediction/markets",
    response_model=PredictionMarketList,
    tags=["prediction"],
    dependencies=[Depends(require_api_key)],
)
def v1_prediction_markets(
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, description="Filter by question/id substring"),
):
    raw = prediction_svc.list_markets(limit=limit, q=q)
    return PredictionMarketList(
        items=[PredictionMarket.model_validate(x) for x in (raw.get("items") or [])],
        total=int(raw.get("total") or 0),
        warnings=list(raw.get("warnings") or []),
    )


@app.get(
    "/v1/prediction/markets/{market_id}",
    response_model=PredictionMarket,
    tags=["prediction"],
    dependencies=[Depends(require_api_key)],
)
def v1_prediction_market(market_id: str):
    mid = (market_id or "").strip()
    if not mid:
        return _prediction_invalid_id("empty market_id")
    try:
        item = prediction_svc.get_market(mid)
    except ValueError as e:
        return _prediction_invalid_id(str(e))
    except LookupError as e:
        return _prediction_not_found(str(e))
    return PredictionMarket.model_validate(item)


@app.get(
    "/v1/prediction/quote",
    response_model=PredictionQuote,
    tags=["prediction"],
    dependencies=[Depends(require_api_key)],
)
def v1_prediction_quote(
    market_id: Optional[str] = Query(None, description="Polymarket market id or POLY:{id}"),
    symbol: Optional[str] = Query(None, description="Alias for market_id, e.g. POLY:559651"),
    id: Optional[str] = Query(None, description="Alias for market_id"),
):
    mid = (market_id or symbol or id or "").strip()
    if not mid:
        return _prediction_invalid_id("empty market_id (use market_id, symbol, or id)")
    try:
        quote = prediction_svc.get_quote(mid)
    except ValueError as e:
        return _prediction_invalid_id(str(e))
    except LookupError as e:
        return _prediction_not_found(str(e))
    return PredictionQuote.model_validate(quote)


if mcp_app is not None:
    app.mount("/mcp", mcp_app)
else:

    @app.get("/mcp", tags=["mcp"])
    @app.get("/mcp/health", tags=["mcp"])
    def mcp_stub():
        return JSONResponse(
            {
                "status": "stub",
                "service": "omnialpha",
                "detail": "fastmcp not installed; install fastmcp for real MCP tools",
                "tools": ["search_instruments", "get_quotes", "get_bars", "get_capabilities", "search_prediction_markets", "get_prediction_market", "get_prediction_quote"],
            }
        )
