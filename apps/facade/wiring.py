"""Composition root: wire vendor adapters into domain ports. Call setup_providers() once."""
from __future__ import annotations

import logging

from domain.marketdata.ports import register_provider
from domain.prediction.ports import register_prediction_provider

log = logging.getLogger(__name__)
_WIRED = False


def setup_providers() -> None:
    """Idempotent: register CN/US/CRYPTO marketdata + POLY prediction provider."""
    global _WIRED
    if _WIRED:
        return

    from adapters.cn_watch import CnTencentAdapter
    from adapters.crypto import OkxCryptoAdapter
    from adapters.polymarket import PolymarketPredictionProvider
    from adapters.us import UsYfinanceAdapter

    register_provider("CN", CnTencentAdapter())
    register_provider("US", UsYfinanceAdapter())
    register_provider("CRYPTO", OkxCryptoAdapter())
    # POLY is prediction-only: do NOT register on marketdata /v1/quotes|/v1/bars
    register_prediction_provider(PolymarketPredictionProvider())

    _WIRED = True
    log.info("providers wired: marketdata=CN,US,CRYPTO; prediction=POLY(polymarket-gamma)")
