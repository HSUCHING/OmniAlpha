"""Normalized L0–L5 data product models (phase-1)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

KNOWN_PREFIXES = ("CN", "US", "CRYPTO", "POLY")
MarketPrefix = Literal["CN", "US", "CRYPTO", "POLY"]
CapabilityName = Literal["watch", "query", "analyze", "screen"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class SymbolId(BaseModel):
    """Canonical symbol id: PREFIX:CODE e.g. CN:600519, US:AAPL."""

    raw: str
    prefix: MarketPrefix
    code: str

    @property
    def canonical(self) -> str:
        return f"{self.prefix}:{self.code}"

    def __str__(self) -> str:
        return self.canonical


class EnvelopeMixin(BaseModel):
    as_of: str = Field(description="UTC ISO8601 timestamp when data was observed/produced")
    source: str = Field(description="Upstream or synthetic source identifier")
    stale: bool = Field(default=False, description="True if served past preferred freshness")


class Instrument(EnvelopeMixin):
    symbol: str = Field(description="Canonical id e.g. CN:600519")
    name: str
    market: MarketPrefix
    exchange: Optional[str] = None
    currency: Optional[str] = None
    asset_class: Optional[str] = None
    active: bool = True


class Quote(EnvelopeMixin):
    symbol: str
    last: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    name: Optional[str] = None


class Bar(EnvelopeMixin):
    symbol: str
    interval: str
    open_time: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class InstrumentList(BaseModel):
    items: list[Instrument]
    total: int


class QuoteList(BaseModel):
    items: list[Quote]
    warnings: list[str] = Field(default_factory=list)


class BarList(BaseModel):
    items: list[Bar]
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    service: str = "omnialpha"
    version: str = "0.1.0"


class CapabilityFlags(BaseModel):
    watch: bool = False
    query: bool = False
    analyze: bool = False
    screen: bool = False
    prediction: bool = False
    provider: Optional[str] = None
    notes: Optional[str] = None


class CapabilitiesResponse(BaseModel):
    phase: str = "phase1"
    markets: dict[str, CapabilityFlags]
    matrix: list[dict]


class ReadyResponse(BaseModel):
    status: str
    postgres: bool
    redis: bool
    service: str = "omnialpha"
    detail: Optional[str] = None



# --- Error (target / post-phase1) ---
# Contract be48ceb / errors.md: ONLY these five codes. Do not add unauthorized/validation_error/etc.
ErrorCode = Literal[
    "not_found",
    "unsupported",
    "stale",
    "invalid_id",
    "rate_limited",
]


class ApiError(BaseModel):
    """统一错误体（目标契约）。phase1 逐步采用。"""

    code: ErrorCode = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable explanation")
    market: Optional[MarketPrefix] = Field(default=None, description="Optional market context")
    capability: Optional[str] = Field(
        default=None, description="Optional capability e.g. watch|query|analyze|screen|prediction"
    )


ReadyCheck = ReadyResponse

SERVICE_NAME = "omnialpha"
SERVICE_VERSION = "0.2.0"


# --- Prediction (POLY) — separate from equity Quote/Bar ---


class PredictionOutcome(BaseModel):
    """Single outcome probability in [0, 1]."""

    name: str
    price: float = Field(ge=0.0, le=1.0, description="Implied probability in [0, 1]")


class PredictionMarket(EnvelopeMixin):
    id: str
    symbol: str = Field(description="Canonical POLY:{id}")
    question: Optional[str] = None
    slug: Optional[str] = None
    active: Optional[bool] = None
    closed: Optional[bool] = None
    outcomes: list[PredictionOutcome] = Field(default_factory=list)
    volume: Optional[float] = None
    liquidity: Optional[float] = None
    end_date: Optional[str] = None


class PredictionMarketList(BaseModel):
    items: list[PredictionMarket]
    total: int
    warnings: list[str] = Field(default_factory=list)


class PredictionQuote(EnvelopeMixin):
    """Prediction probability quote — not equity Quote."""

    market_id: str
    symbol: str
    question: Optional[str] = None
    outcomes: list[PredictionOutcome] = Field(default_factory=list)
    yes_price: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    no_price: Optional[float] = Field(default=None, ge=0.0, le=1.0)
