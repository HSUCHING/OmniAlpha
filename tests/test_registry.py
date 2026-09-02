"""Unit tests for adapter registry routing."""
from __future__ import annotations

from adapters.registry import (
    capabilities,
    get_adapter,
    setup_providers,
    supported_markets,
)


def test_registry_registers_four_markets():
    setup_providers()
    markets = supported_markets()
    assert markets == ["CN", "CRYPTO", "POLY", "US"]
    for m in markets:
        ad = get_adapter(m)
        assert ad is not None
        assert ad.market == m


def test_get_adapter_unknown_returns_none():
    setup_providers()
    assert get_adapter("FX") is None


def test_capabilities_analyze_screen_false():
    caps = capabilities()
    for market, flags in caps.items():
        assert flags["analyze"] is False
        assert flags["screen"] is False
        assert flags["prediction"] is False
    assert caps["CN"]["quotes"] is True
    assert caps["POLY"]["bars"] is False


def test_domain_marketdata_uses_registry():
    import inspect

    import domain.marketdata.service as svc

    src = inspect.getsource(svc)
    assert "get_adapter" in src
    assert "qt.gtimg.cn" not in src


def test_ports_mirror_registry():
    from domain.marketdata.ports import get_provider

    setup_providers()
    assert get_provider("US") is get_adapter("US")
