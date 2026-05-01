from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from main import app
from routers.deps import get_csv_service, get_price_service
from services.calculator import calculate_trade_financials, compute_portfolio
from services.csv_service import CsvService


client = TestClient(app)


@pytest.fixture(autouse=True)
def stable_discount_rate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(CsvService, "get_commission_discount_rate", lambda self: 0.0)


def test_settings_endpoint_returns_commission_discount():
    response = client.get("/api/settings")

    assert response.status_code == 200
    assert response.json() == {
        "commission_discount_rate": get_csv_service().get_commission_discount_rate()
    }


def test_transactions_endpoint_returns_paginated_rows():
    response = client.get("/api/transactions?page=1&page_size=10")

    assert response.status_code == 200
    body = response.json()
    expected = get_csv_service().read_transactions()
    assert body["total"] == len(expected)
    assert len(body["items"]) == 10
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
    service = get_csv_service()
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
        params={"action": "買", "amount": 100000, "trade_type": "一般"},
    )

    assert response.status_code == 200
    expected = calculate_trade_financials(
        action="買",
        trade_type="一般",
        amount=100000,
        discount_rate=get_csv_service().get_commission_discount_rate(),
    )
    assert response.json()["discounted_fee"] == expected.discounted_fee
    assert response.json()["expense"] == expected.expense
