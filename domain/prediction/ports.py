"""Prediction ports — domain-owned."""
from __future__ import annotations

from typing import Any, Optional, Protocol

_provider: Optional["PredictionProvider"] = None


class PredictionProvider(Protocol):
    def list_markets(self, limit: int = 20, q: Optional[str] = None) -> Any: ...
    def get_market(self, market_id: str) -> Any: ...


def register_prediction_provider(provider: PredictionProvider) -> None:
    global _provider
    _provider = provider


def get_prediction_provider() -> Optional[PredictionProvider]:
    return _provider
