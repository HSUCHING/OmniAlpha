"""Unit tests for apps facade wiring + domain ports."""
from __future__ import annotations

from apps.facade.wiring import setup_providers
from domain.marketdata.ports import clear_providers, get_provider, list_registered_markets
from domain.meta import get_capabilities_matrix


def test_wiring_registers_cn_us_crypto_only():
    clear_providers()
    import apps.facade.wiring as w
    w._WIRED = False
    setup_providers()
    markets = list_registered_markets()
    assert markets == ["CN", "CRYPTO", "US"]
    assert get_provider("CN") is not None
    assert get_provider("US") is not None
    assert get_provider("CRYPTO") is not None
    assert get_provider("POLY") is None


def test_setup_providers_idempotent():
    clear_providers()
    import apps.facade.wiring as w
    w._WIRED = False
    setup_providers()
    setup_providers()
    assert list_registered_markets() == ["CN", "CRYPTO", "US"]


def test_capabilities_poly_and_analyze_screen_unsupported():
    m = get_capabilities_matrix()
    assert m["matrix"]["POLY"]["watch"]["status"] == "unsupported"
    assert m["matrix"]["POLY"]["query"]["status"] == "unsupported"
    for market, caps in m["matrix"].items():
        assert caps["analyze"]["status"] == "unsupported"
        assert caps["screen"]["status"] == "unsupported"
    assert m["detail"]["POLY"]["prediction"] is False
    assert m["matrix"]["CRYPTO"]["watch"]["source"] == "okx"


def test_domain_marketdata_uses_ports_not_adapters():
    import inspect
    import domain.marketdata.service as svc

    src = inspect.getsource(svc)
    assert "get_provider" in src
    assert "from adapters" not in src
    assert "import adapters" not in src
    assert "qt.gtimg.cn" not in src
