"""Composition root: wire vendor adapters into domain ports. Call setup_providers() once."""
from __future__ import annotations

import logging

from domain.marketdata.ports import register_provider

log = logging.getLogger(__name__)
_WIRED = False


def setup_providers() -> None:
    """Idempotent: register CN/US/CRYPTO marketdata providers only (phase-1)."""
    global _WIRED
    if _WIRED:
        return

    from adapters.cn_watch import CnTencentAdapter
    from adapters.crypto import OkxCryptoAdapter
    from adapters.us import UsYfinanceAdapter

    register_provider("CN", CnTencentAdapter())
    register_provider("US", UsYfinanceAdapter())
    register_provider("CRYPTO", OkxCryptoAdapter())
    # POLY equity marketdata: not registered in phase-1
    # Prediction provider: not registered / not advertised in phase-1

    _WIRED = True
    log.info("providers wired: marketdata=CN,US,CRYPTO; POLY/prediction deferred")
