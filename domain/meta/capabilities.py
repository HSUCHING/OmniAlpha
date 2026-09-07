"""Machine-readable market × capability matrix (phase-1 reality)."""
from __future__ import annotations

from typing import Any, Literal

CapabilityStatus = Literal["implemented", "partial", "unsupported"]

CAPABILITIES = ("watch", "query", "analyze", "screen", "prediction")
MARKETS = ("CN", "US", "CRYPTO", "POLY")


def get_capabilities_matrix() -> dict[str, Any]:
    """Reflect phase-1 reality for eval / clients. analyze/screen never implemented."""
    matrix = {
        "CN": {
            "watch": {"status": "implemented", "source": "tencent", "notes": "quotes+bars"},
            "query": {"status": "implemented", "source": "postgres", "notes": "instruments"},
            "analyze": {"status": "unsupported"},
            "screen": {"status": "unsupported"},
            "prediction": {"status": "unsupported"},
        },
        "US": {
            "watch": {"status": "implemented", "source": "yfinance", "notes": "quotes+bars"},
            "query": {"status": "implemented", "source": "postgres", "notes": "instruments"},
            "analyze": {"status": "unsupported"},
            "screen": {"status": "unsupported"},
            "prediction": {"status": "unsupported"},
        },
        "CRYPTO": {
            "watch": {"status": "implemented", "source": "okx", "notes": "quotes+bars via OKX public REST (httpx)"},
            "query": {"status": "implemented", "source": "postgres", "notes": "instruments"},
            "analyze": {"status": "unsupported"},
            "screen": {"status": "unsupported"},
            "prediction": {"status": "unsupported"},
        },
        "POLY": {
            "watch": {
                "status": "unsupported",
                "notes": "POLY is prediction-only; do not use equity Quote/Bar path",
            },
            "query": {
                "status": "unsupported",
                "notes": "instruments seed may exist in PG; market product query unsupported",
            },
            "analyze": {"status": "unsupported"},
            "screen": {"status": "unsupported"},
            "prediction": {
                "status": "implemented",
                "source": "polymarket-gamma",
                "notes": "/v1/prediction/* + MCP Prediction* tools; not via /v1/quotes|/v1/bars",
            },
        },
    }
    flat = []
    for market in MARKETS:
        for cap in CAPABILITIES:
            cell = matrix[market][cap]
            flat.append(
                {
                    "market": market,
                    "capability": cap,
                    "status": cell["status"],
                    "source": cell.get("source"),
                    "notes": cell.get("notes"),
                }
            )
    detail = {
        "CN": {"instruments": True, "quotes": True, "bars": True, "prediction": False},
        "US": {"instruments": True, "quotes": True, "bars": True, "prediction": False},
        "CRYPTO": {"instruments": True, "quotes": True, "bars": True, "prediction": False},
        "POLY": {"instruments": True, "quotes": False, "bars": False, "prediction": True},
    }
    return {
        "version": "0.2.0",
        "phase": "phase1",
        "markets": list(MARKETS),
        "capabilities": list(CAPABILITIES),
        "matrix": matrix,
        "items": flat,
        "detail": detail,
        "notes": [
            "analyze and screen are unsupported; HTTP routes return 501",
            "POLY prediction implemented via /v1/prediction/* (source=polymarket-gamma); equity watch/query unsupported",
            "CRYPTO watch source is okx via httpx (not ccxt)",
        ],
    }
