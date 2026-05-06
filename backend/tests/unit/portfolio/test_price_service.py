from __future__ import annotations

import time
from datetime import date

import pandas as pd
import pytest

from backend.domain.portfolio.price_service import PriceService
from backend.infrastructure.market_data.yfinance_quote_provider import YfinanceQuoteProvider
from backend.models.domain.portfolio import PriceQuote, StockLookup


@pytest.mark.asyncio
async def test_get_prices_trims_codes_and_uses_stock_names(monkeypatch: pytest.MonkeyPatch):
    service = PriceService()
    calls: list[tuple[list[str], dict[str, str]]] = []

    async def fake_fetch_batch(codes: list[str], stock_names: dict[str, str]) -> None:
        calls.append((codes, stock_names))
        expire = time.monotonic() + service._TTL
        for code in codes:
            service._cache[code] = (
                expire,
                PriceQuote(code=code, name=stock_names.get(code), price=100.0, delayed=False, source="test"),
            )

    monkeypatch.setattr(service, "_fetch_batch", fake_fetch_batch)

    quotes = await service.get_prices(
        [" 2330 ", "", "2317"],
        [StockLookup(code="2330", name="台積電"), StockLookup(code="2317", name="鴻海")],
    )

    assert [quote.code for quote in quotes] == ["2330", "2317"]
    assert [quote.name for quote in quotes] == ["台積電", "鴻海"]
    assert calls == [(["2330", "2317"], {"2330": "台積電", "2317": "鴻海"})]


@pytest.mark.asyncio
async def test_get_price_caches_successful_batch_result(monkeypatch: pytest.MonkeyPatch):
    service = PriceService()
    calls: list[list[str]] = []

    async def fake_fetch_batch(codes: list[str], stock_names: dict[str, str]) -> None:
        calls.append(codes)
        service._cache["2330"] = (
            time.monotonic() + service._TTL,
            PriceQuote(code="2330", name=stock_names["2330"], price=123.0, delayed=False, source="test"),
        )

    monkeypatch.setattr(service, "_fetch_batch", fake_fetch_batch)

    first = await service.get_price("2330", "台積電")
    second = await service.get_price("2330", "台積電")

    assert first.price == pytest.approx(123.0)
    assert second.price == pytest.approx(123.0)
    assert calls == [["2330"]]


@pytest.mark.asyncio
async def test_get_price_falls_back_to_delayed_quote_when_batch_has_no_data(monkeypatch: pytest.MonkeyPatch):
    service = PriceService()

    async def fake_fetch_batch(codes: list[str], stock_names: dict[str, str]) -> None:
        return None

    monkeypatch.setattr(service, "_fetch_batch", fake_fetch_batch)

    quote = await service.get_price("9999", "測試股")

    assert quote.code == "9999"
    assert quote.name == "測試股"
    assert quote.price is None
    assert quote.delayed is True


def test_yfinance_provider_prefers_tw_ticker_and_sets_previous_close(monkeypatch: pytest.MonkeyPatch):
    provider = YfinanceQuoteProvider()

    frame = pd.DataFrame(
        {
            ("Close", "2330.TW"): [980.0, 988.0],
            ("Close", "2330.TWO"): [None, None],
        }
    )

    monkeypatch.setattr(
        "backend.infrastructure.market_data.yfinance_quote_provider.yf.download",
        lambda *args, **kwargs: frame,
    )

    quotes = provider.fetch_quotes(["2330"], {"2330": "台積電"})

    assert len(quotes) == 1
    quote = quotes[0]
    assert quote.code == "2330"
    assert quote.name == "台積電"
    assert quote.price == pytest.approx(988.0)
    assert quote.previous_close == pytest.approx(980.0)
    assert quote.delayed is False
    assert quote.source == "yfinance"


def test_yfinance_provider_returns_delayed_quote_on_exception(monkeypatch: pytest.MonkeyPatch):
    provider = YfinanceQuoteProvider()

    def fail_download(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "backend.infrastructure.market_data.yfinance_quote_provider.yf.download",
        fail_download,
    )

    quotes = provider.fetch_quotes(["2330"], {"2330": "台積電"})

    assert len(quotes) == 1
    quote = quotes[0]
    assert quote.price is None
    assert quote.delayed is True
    assert quote.name == "台積電"


def test_yfinance_provider_falls_back_to_two_ticker(monkeypatch: pytest.MonkeyPatch):
    provider = YfinanceQuoteProvider()

    frame = pd.DataFrame(
        {
            ("Close", "1234.TW"): [None, None],
            ("Close", "1234.TWO"): [10.0, 11.5],
        }
    )

    monkeypatch.setattr(
        "backend.infrastructure.market_data.yfinance_quote_provider.yf.download",
        lambda *args, **kwargs: frame,
    )

    [quote] = provider.fetch_quotes(["1234"], {"1234": "測試股"})

    assert quote.code == "1234"
    assert quote.price == pytest.approx(11.5)
    assert quote.previous_close == pytest.approx(10.0)
    assert quote.delayed is False


def test_yfinance_provider_returns_delayed_quote_when_close_is_missing(monkeypatch: pytest.MonkeyPatch):
    provider = YfinanceQuoteProvider()

    monkeypatch.setattr(
        "backend.infrastructure.market_data.yfinance_quote_provider.yf.download",
        lambda *args, **kwargs: pd.DataFrame({"Open": [1.0, 2.0]}),
    )

    [quote] = provider.fetch_quotes(["2330"], {"2330": "台積電"})

    assert quote.code == "2330"
    assert quote.price is None
    assert quote.delayed is True


def test_yfinance_provider_returns_none_for_future_benchmark_start_date():
    provider = YfinanceQuoteProvider()

    assert provider.get_benchmark_return_rate("0050.TW", date(2999, 1, 1)) is None


def test_yfinance_provider_uses_first_close_on_or_after_start_date(monkeypatch: pytest.MonkeyPatch):
    provider = YfinanceQuoteProvider()

    history = pd.DataFrame(
        {"Close": [90.0, 100.0, 120.0]},
        index=pd.to_datetime(["2026-01-03", "2026-01-10", "2026-01-15"]),
    )

    class FakeTicker:
        def history(self, **kwargs):
            return history

    monkeypatch.setattr(
        "backend.infrastructure.market_data.yfinance_quote_provider.yf.Ticker",
        lambda ticker: FakeTicker(),
    )

    result = provider.get_benchmark_return_rate("0050.TW", date(2026, 1, 10))

    assert result == pytest.approx(0.2)


def test_yfinance_provider_falls_back_to_last_close_when_start_date_has_no_future_rows(monkeypatch: pytest.MonkeyPatch):
    provider = YfinanceQuoteProvider()

    history = pd.DataFrame(
        {"Close": [90.0, 100.0]},
        index=pd.to_datetime(["2026-01-03", "2026-01-05"]),
    )

    class FakeTicker:
        def history(self, **kwargs):
            return history

    monkeypatch.setattr(
        "backend.infrastructure.market_data.yfinance_quote_provider.yf.Ticker",
        lambda ticker: FakeTicker(),
    )

    result = provider.get_benchmark_return_rate("0050.TW", date(2026, 1, 10))

    assert result == pytest.approx(0.0)
