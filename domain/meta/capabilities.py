"""Machine-readable market × capability matrix (phase-1 reality)."""
from __future__ import annotations

from typing import Any, Literal

CapabilityStatus = Literal["implemented", "partial", "unsupported"]

# Eval scenarios use watch/query/analyze/screen; also expose instruments/quotes/bars aliases in items notes.
CAPABILITIES = ("watch", "query", "analyze", "screen")
MARKETS = ("CN", "US", "CRYPTO", "POLY")


def get_capabilities_matrix() -> dict[str, Any]:
    """Reflect phase-1 reality for eval / clients. analyze/screen never implemented."""
    matrix = {
        "CN": {
            "watch": {"status": "implemented", "source": "tencent", "notes": "quotes+bars"},
            "query": {"status": "implemented", "source": "postgres", "notes": "instruments"},
            "analyze": {"status": "unsupported"},
            "screen": {"status": "unsupported"},
        },
        "US": {
            "watch": {"status": "implemented", "source": "yfinance", "notes": "quotes+bars"},
            "query": {"status": "implemented", "source": "postgres", "notes": "instruments"},
            "analyze": {"status": "unsupported"},
            "screen": {"status": "unsupported"},
        },
        "CRYPTO": {
            "watch": {"status": "implemented", "source": "okx", "notes": "quotes+bars via OKX public REST (httpx)"},
            "query": {"status": "implemented", "source": "postgres", "notes": "instruments"},
            "analyze": {"status": "unsupported"},
            "screen": {"status": "unsupported"},
        },
        "POLY": {
            "watch": {
                "status": "partial",
                "source": "polymarket",
                "notes": "POLY:{id} Quote.last=probability via /v1/quotes; bars empty/synthetic",
            },
            "query": {
                "status": "implemented",
                "source": "postgres",
                "notes": "instruments seed; thin /v1/prediction/* helpers exist but prediction product not advertised",
            },
            "analyze": {"status": "unsupported"},
            "screen": {"status": "unsupported"},
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
    # Extra detail: POLY instruments seed may exist but watch/query product = unsupported
    detail = {
        "CN": {"instruments": True, "quotes": True, "bars": True, "prediction": False},
        "US": {"instruments": True, "quotes": True, "bars": True, "prediction": False},
        "CRYPTO": {"instruments": True, "quotes": True, "bars": True, "prediction": False},
        "POLY": {"instruments": True, "quotes": True, "bars": False, "prediction": False},
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
            "POLY Quote.last is outcome probability in [0,1] (source=polymarket); prediction product not advertised",
            "CRYPTO watch source is okx via httpx (not ccxt)",
        ],
    }
