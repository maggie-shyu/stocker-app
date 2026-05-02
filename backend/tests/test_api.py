from unittest.mock import AsyncMock
from datetime import date

import pytest
from fastapi.testclient import TestClient

from config import get_settings
from main import app
from models.schemas import TransactionRecord
from routers.deps import get_price_service
from services.calculator import calculate_trade_financials, compute_portfolio
from services.csv_service import CsvService

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
_test_svc = CsvService(get_settings().data_dir / "tommy")

client = TestClient(app)


@pytest.fixture(autouse=True)
def stable_discount_rate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(CsvService, "get_commission_discount_rate", lambda self: 0.0)
    monkeypatch.setattr(CsvService, "read_stocks", lambda self: [])


@pytest.fixture(autouse=True)
def override_auth():
    from routers.deps import get_current_user, get_supabase_service

    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID
    app.dependency_overrides[get_supabase_service] = lambda: _test_svc
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_supabase_service, None)


def test_settings_endpoint_returns_commission_discount():
    response = client.get("/api/settings")

    assert response.status_code == 200
    assert response.json() == {
        "commission_discount_rate": _test_svc.get_commission_discount_rate()
    }


def test_transactions_endpoint_returns_paginated_rows():
    response = client.get("/api/transactions?page=1&page_size=10")

    assert response.status_code == 200
    body = response.json()
    expected = _test_svc.read_transactions()
    assert body["total"] == len(expected)
    assert len(body["items"]) == min(10, len(expected))
    assert body["items"][0]["code"] == expected[0].code


def test_dashboard_endpoint_returns_kpis_and_recent_transactions():
    # mock price service to return no live prices (price-independent assertions only)
    mock_svc = AsyncMock()
    mock_svc.get_prices.return_value = []
    app.dependency_overrides[get_price_service] = lambda: mock_svc
    try:
        response = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.pop(get_price_service, None)

    assert response.status_code == 200
    body = response.json()
    service = _test_svc
    transactions = service.read_transactions()
    portfolio = compute_portfolio(
        transactions=transactions,
        cashflows=service.read_cashflows(),
    )
    code_count = len({tx.code for tx in transactions})
    assert body["principal"] == portfolio.principal
    assert body["investment_years"] == pytest.approx(portfolio.investment_years)
    assert body["cash_balance"] == pytest.approx(portfolio.cash_balance)
    assert body["realized_pnl"] == pytest.approx(portfolio.realized_pnl)
    assert body["realized_pnl_rate"] == pytest.approx(portfolio.realized_pnl_rate)
    assert body["annualized_return_rate"] == pytest.approx(portfolio.annualized_return_rate)
    assert body["dividend_income"] == pytest.approx(portfolio.dividend_income)
    assert len(body["holdings_pie"]) == len(portfolio.holdings)
    assert len(body["recent_transactions"]) == 3
    assert body["price_status"] == {"total": code_count, "priced": 0, "delayed": code_count}


def test_stock_fee_preview_endpoint():
    response = client.get(
        "/api/stocks/preview-fee",
        params={"action": "買", "shares": 1000, "amount": 100000, "trade_type": "一般"},
    )

    assert response.status_code == 200
    expected = calculate_trade_financials(
        action="買",
        trade_type="一般",
        shares=1000,
        amount=100000,
        discount_rate=_test_svc.get_commission_discount_rate(),
    )
    assert response.json()["discounted_fee"] == expected.discounted_fee
    assert response.json()["expense"] == expected.expense


def test_stock_fee_preview_endpoint_uses_odd_lot_minimum():
    response = client.get(
        "/api/stocks/preview-fee",
        params={"action": "買", "shares": 1, "amount": 10, "trade_type": "一般"},
    )

    assert response.status_code == 200
    expected = calculate_trade_financials(
        action="買",
        trade_type="一般",
        shares=1,
        amount=10,
        discount_rate=_test_svc.get_commission_discount_rate(),
    )
    assert response.json()["discounted_fee"] == expected.discounted_fee
    assert response.json()["expense"] == expected.expense


def test_stock_fee_preview_endpoint_uses_etf_tax_rate():
    response = client.get(
        "/api/stocks/preview-fee",
        params={"action": "賣", "code": "0050", "shares": 1000, "amount": 100000, "trade_type": "一般"},
    )

    assert response.status_code == 200
    expected = calculate_trade_financials(
        action="賣",
        code="0050",
        trade_type="一般",
        shares=1000,
        amount=100000,
        discount_rate=_test_svc.get_commission_discount_rate(),
    )
    assert response.json()["tax"] == expected.tax


def test_realized_endpoint_only_counts_dividends_before_last_sell(monkeypatch: pytest.MonkeyPatch):
    txs = [
        TransactionRecord(
            id="1",
            date=date(2026, 1, 1),
            action="買",
            code="2330",
            name="台積電",
            buy_shares=100,
            buy_price=100,
            expense=10020,
        ),
        TransactionRecord(
            id="2",
            date=date(2026, 1, 2),
            action="股利",
            code="2330",
            name="台積電",
            income=300,
            amount=300,
        ),
        TransactionRecord(
            id="3",
            date=date(2026, 1, 3),
            action="賣",
            code="2330",
            name="台積電",
            sell_shares=50,
            sell_price=120,
            income=5971,
        ),
        TransactionRecord(
            id="4",
            date=date(2026, 1, 4),
            action="股利",
            code="2330",
            name="台積電",
            income=500,
            amount=500,
        ),
    ]
    monkeypatch.setattr(_test_svc, "read_transactions", lambda: txs)
    monkeypatch.setattr(_test_svc, "read_cashflows", lambda: [])

    response = client.get("/api/realized")

    assert response.status_code == 200
    body = response.json()
    assert body["dividend_income"] == pytest.approx(300)
    assert body["dividend_by_stock"] == [{"code": "2330", "name": "台積電", "dividend_income": 300}]
    assert body["items"][0]["avg_buy_price"] == pytest.approx(100)
    assert body["items"][0]["avg_sell_price"] == pytest.approx(120)
