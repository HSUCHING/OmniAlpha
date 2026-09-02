"""Prediction ports: domain interface; adapters register implementations."""
from __future__ import annotations

from typing import Any, Optional, Protocol


class PredictionProvider(Protocol):
    def list_markets(self, limit: int = 20, q: Optional[str] = None) -> list[dict[str, Any]]: ...

    def get_market(self, market_id: str) -> Optional[dict[str, Any]]: ...


_PROVIDER: Optional[PredictionProvider] = None


def register_prediction_provider(provider: PredictionProvider) -> None:
    global _PROVIDER
    _PROVIDER = provider


def get_prediction_provider() -> Optional[PredictionProvider]:
    return _PROVIDER
