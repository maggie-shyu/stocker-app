from __future__ import annotations

import pytest

from backend.models.schemas import PriceQuote, StockLookup
from backend.services.price_service import PriceService


@pytest.mark.asyncio
async def test_get_prices_trims_codes_and_uses_stock_names(monkeypatch: pytest.MonkeyPatch):
    service = PriceService()
    calls: list[tuple[str, str | None]] = []

    async def fake_get_price(code: str, name: str | None = None) -> PriceQuote:
        calls.append((code, name))
        return PriceQuote(code=code, name=name, price=100.0, delayed=False)

    monkeypatch.setattr(service, "get_price", fake_get_price)

    quotes = await service.get_prices(
        [" 2330 ", "", "2317"],
        [StockLookup(code="2330", name="台積電"), StockLookup(code="2317", name="鴻海")],
    )

    assert [quote.code for quote in quotes] == ["2330", "2317"]
    assert calls == [("2330", "台積電"), ("2317", "鴻海")]


@pytest.mark.asyncio
async def test_get_price_caches_successful_market_result(monkeypatch: pytest.MonkeyPatch):
    service = PriceService()
    calls: list[tuple[str, str, str | None]] = []

    async def fake_fetch(code: str, market: str, name: str | None) -> PriceQuote:
        calls.append((code, market, name))
        if market == "tse":
            return PriceQuote(code=code, name=name, price=123.0, delayed=False, source="twse:tse")
        return PriceQuote(code=code, name=name, price=None, delayed=True)

    monkeypatch.setattr(service, "_fetch_market_price", fake_fetch)

    first = await service.get_price("2330", "台積電")
    second = await service.get_price("2330", "台積電")

    assert first.price == pytest.approx(123.0)
    assert second.price == pytest.approx(123.0)
    assert calls == [("2330", "tse", "台積電")]


@pytest.mark.asyncio
async def test_get_price_falls_back_to_delayed_quote_when_markets_missing(monkeypatch: pytest.MonkeyPatch):
    service = PriceService()

    async def fake_fetch(code: str, market: str, name: str | None) -> PriceQuote:
        return PriceQuote(code=code, name=name, price=None, delayed=True)

    monkeypatch.setattr(service, "_fetch_market_price", fake_fetch)

    quote = await service.get_price("9999", "測試股")

    assert quote.code == "9999"
    assert quote.name == "測試股"
    assert quote.price is None
    assert quote.delayed is True


@pytest.mark.asyncio
async def test_fetch_market_price_uses_fallback_price_field(monkeypatch: pytest.MonkeyPatch):
    service = PriceService()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"msgArray": [{"n": "台積電", "z": "-", "y": "988"}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, params):
            return FakeResponse()

    monkeypatch.setattr("backend.services.price_service.httpx.AsyncClient", FakeClient)

    quote = await service._fetch_market_price("2330", "tse", "台積電")

    assert quote.price == pytest.approx(988.0)
    assert quote.delayed is False
    assert quote.source == "twse:tse"


@pytest.mark.asyncio
async def test_fetch_market_price_returns_delayed_quote_on_exception(monkeypatch: pytest.MonkeyPatch):
    service = PriceService()

    class FailingClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, params):
            raise RuntimeError("boom")

    monkeypatch.setattr("backend.services.price_service.httpx.AsyncClient", FailingClient)

    quote = await service._fetch_market_price("2330", "tse", "台積電")

    assert quote.price is None
    assert quote.delayed is True
    assert quote.name == "台積電"
