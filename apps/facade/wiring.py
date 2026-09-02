"""Composition root: delegates to adapters.registry (single source of truth)."""
from __future__ import annotations

from adapters.registry import ensure_registered, setup_providers

__all__ = ["setup_providers", "ensure_registered"]
