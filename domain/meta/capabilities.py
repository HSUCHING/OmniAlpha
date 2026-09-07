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
            # Product口径: Polymarket = 预测*市场*行情 → watch/query。
            # capability "prediction" 留给自研模型预测，不表示交易所行情。
            "watch": {
                "status": "implemented",
                "source": "polymarket-gamma",
                "notes": "market odds via /v1/prediction/quote (Event/Market/Outcome; not equity Quote/Bar)",
            },
            "query": {
                "status": "implemented",
                "source": "polymarket-gamma",
                "notes": "search/list markets via /v1/prediction/markets (path name legacy; semantics=query)",
            },
            "analyze": {"status": "unsupported"},
            "screen": {"status": "unsupported"},
            "prediction": {
                "status": "unsupported",
                "notes": "reserved for first-party model forecasts; Polymarket venue data is watch/query",
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
        "POLY": {"instruments": False, "quotes": False, "bars": False, "markets": True, "odds": True, "prediction": False},
    }
    return {
        "version": "0.2.1",
        "phase": "phase1",
        "markets": list(MARKETS),
        "capabilities": list(CAPABILITIES),
        "matrix": matrix,
        "items": flat,
        "detail": detail,
        "notes": [
            "analyze and screen are unsupported; HTTP routes return 501",
            "POLY watch/query = Polymarket venue data via /v1/prediction/* (Gamma); capability prediction reserved for model forecasts",
            "CRYPTO watch source is okx via httpx (not ccxt)",
        ],
    }
