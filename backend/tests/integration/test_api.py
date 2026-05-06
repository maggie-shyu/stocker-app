from unittest.mock import AsyncMock
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.api.deps import get_admin_service, get_price_service
from backend.api import deps as deps_router, stocks as stocks_router
from backend.domain.portfolio.calculator import calculate_trade_financials, compute_portfolio
from backend.models.api.auth import AuthenticatedUser
from backend.models.domain.ledger import CashflowRecord, TransactionRecord, UserSettings
from backend.tests.support.fixture_ledger_store import FixtureLedgerStore

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_test_svc = FixtureLedgerStore(TEST_DATA_DIR)


class TestAdminService:
    def get_overview(self):
        return {
            "total_users": 3,
            "users_with_transactions": 2,
            "users_with_cashflows": 2,
            "supabase_memory_usage_percent": 58.0,
            "cpu_busy_percent": 42.0,
            "disk_usage_percent": 75.0,
            "connection_rate_percent": 70.0,
            "active_queries": 12,
        }

    def list_tables(self):
        return [
            {
                "name": "transactions",
                "label": "交易紀錄",
                "description": "All transaction rows across users.",
                "row_count": 5,
            },
            {
                "name": "user_settings",
                "label": "使用者設定",
                "description": "Per-user settings rows.",
                "row_count": 3,
            },
        ]

    def read_table(self, table_name: str, *, page: int, page_size: int):
        if table_name != "transactions":
            raise KeyError(table_name)
        return {
            "table_name": "transactions",
            "label": "交易紀錄",
            "page": page,
            "page_size": page_size,
            "total": 73,
            "columns": ["id", "user_id", "code"],
            "items": (
                [
                    {"id": "tx-26", "user_id": TEST_USER_ID, "code": "2603"},
                    {"id": "tx-27", "user_id": TEST_USER_ID, "code": "0050"},
                ]
                if page == 2
                else [
                    {"id": "tx-1", "user_id": TEST_USER_ID, "code": "2330"},
                    {"id": "tx-2", "user_id": TEST_USER_ID, "code": "2317"},
                ]
            ),
        }

_test_admin_svc = TestAdminService()

client = TestClient(app)


@pytest.fixture(autouse=True)
def stable_discount_rate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(FixtureLedgerStore, "get_settings", lambda self: UserSettings(commission_discount_rate=0.0))
    monkeypatch.setattr(FixtureLedgerStore, "read_stocks", lambda self: [])


@pytest.fixture(autouse=True)
def override_auth():
    from backend.api.deps import get_current_user, get_ledger_store, get_stock_catalog

    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=TEST_USER_ID,
        email="admin@example.com",
    )
    app.dependency_overrides[get_ledger_store] = lambda: _test_svc
    app.dependency_overrides[get_stock_catalog] = lambda: _test_svc
    app.dependency_overrides[get_admin_service] = lambda: _test_admin_svc
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_ledger_store, None)
    app.dependency_overrides.pop(get_stock_catalog, None)
    app.dependency_overrides.pop(get_admin_service, None)


def test_settings_endpoint_returns_commission_discount():
    response = client.get("/api/settings")

    assert response.status_code == 200
    assert response.json()["commission_discount_rate"] == _test_svc.get_settings().commission_discount_rate


def test_admin_capabilities_endpoint_reports_admin_status(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps_router,
        "get_settings",
        lambda: SimpleNamespace(admin_email_allowlist=["admin@example.com"]),
    )

    response = client.get("/api/admin/capabilities")

    assert response.status_code == 200
    assert response.json() == {"is_admin": True}


def test_admin_capabilities_endpoint_reports_non_admin_for_other_emails(monkeypatch: pytest.MonkeyPatch):
    from backend.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=TEST_USER_ID,
        email="member@example.com",
    )
    monkeypatch.setattr(
        deps_router,
        "get_settings",
        lambda: SimpleNamespace(admin_email_allowlist=["admin@example.com"]),
    )

    response = client.get("/api/admin/capabilities")

    assert response.status_code == 200
    assert response.json() == {"is_admin": False}


def test_admin_overview_endpoint_requires_admin(monkeypatch: pytest.MonkeyPatch):
    from backend.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=TEST_USER_ID,
        email="member@example.com",
    )
    monkeypatch.setattr(
        deps_router,
        "get_settings",
        lambda: SimpleNamespace(admin_email_allowlist=["admin@example.com"]),
    )

    response = client.get("/api/admin/overview")

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_endpoints_return_overview_and_table_data(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps_router,
        "get_settings",
        lambda: SimpleNamespace(admin_email_allowlist=["admin@example.com"]),
    )

    overview = client.get("/api/admin/overview")
    tables = client.get("/api/admin/tables")
    table_rows = client.get("/api/admin/tables/transactions", params={"page": 1, "page_size": 2})

    assert overview.status_code == 200
    assert overview.json()["total_users"] == 3
    assert overview.json()["disk_usage_percent"] == 75.0
    assert overview.json()["connection_rate_percent"] == 70.0
    assert overview.json()["active_queries"] == 12
    assert overview.json()["supabase_memory_usage_percent"] == 58.0
    assert tables.status_code == 200
    assert tables.json()[0]["name"] == "transactions"
    assert table_rows.status_code == 200
    assert table_rows.json()["columns"] == ["id", "user_id", "code"]
    assert table_rows.json()["items"][0]["code"] == "2330"


def test_admin_table_endpoint_supports_pagination(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps_router,
        "get_settings",
        lambda: SimpleNamespace(admin_email_allowlist=["admin@example.com"]),
    )

    response = client.get("/api/admin/tables/transactions", params={"page": 2, "page_size": 2})

    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["items"][0]["code"] == "2603"


def test_transactions_endpoint_returns_paginated_rows():
    response = client.get("/api/transactions?page=1&page_size=10")

    assert response.status_code == 200
    body = response.json()
    expected = _test_svc.read_transactions()
    assert body["total"] == len(expected)
    assert len(body["items"]) == min(10, len(expected))
    assert body["items"][0]["code"] == expected[0].code


def test_transactions_endpoint_applies_filters():
    response = client.get(
        "/api/transactions",
        params={
            "action": "股利",
            "code": "6274",
            "from_date": "2026-04-01",
            "to_date": "2026-04-30",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["action"] == "股利"
    assert body["items"][0]["code"] == "6274"


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
        settings=_test_svc.get_settings(),
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
        settings=_test_svc.get_settings(),
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
        settings=_test_svc.get_settings(),
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
    assert body["dividend_income"] == pytest.approx(800)
    assert body["dividend_by_stock"] == [{"code": "2330", "name": "台積電", "dividend_income": 800}]
    assert body["items"][0]["avg_buy_price"] == pytest.approx(100)
    assert body["items"][0]["avg_sell_price"] == pytest.approx(120)


def test_realized_endpoint_applies_code_and_date_filters(monkeypatch: pytest.MonkeyPatch):
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
            date=date(2026, 1, 5),
            action="賣",
            code="2330",
            name="台積電",
            sell_shares=100,
            sell_price=120,
            income=11964,
        ),
        TransactionRecord(
            id="3",
            date=date(2026, 1, 2),
            action="買",
            code="2317",
            name="鴻海",
            buy_shares=100,
            buy_price=90,
            expense=9020,
        ),
        TransactionRecord(
            id="4",
            date=date(2026, 1, 6),
            action="賣",
            code="2317",
            name="鴻海",
            sell_shares=100,
            sell_price=95,
            income=9466,
        ),
        TransactionRecord(
            id="5",
            date=date(2026, 1, 4),
            action="股利",
            code="2330",
            name="台積電",
            income=200,
            amount=200,
        ),
    ]
    monkeypatch.setattr(_test_svc, "read_transactions", lambda: txs)
    monkeypatch.setattr(_test_svc, "read_cashflows", lambda: [])

    response = client.get(
        "/api/realized",
        params={"code": "2330", "from_date": "2026-01-03", "to_date": "2026-01-05"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["code"] == "2330"
    assert body["dividend_income"] == pytest.approx(200)
    assert body["dividend_by_stock"] == [{"code": "2330", "name": "台積電", "dividend_income": 200}]


def test_prices_endpoint_rejects_too_many_codes(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        stocks_router,
        "get_settings",
        lambda: type("Settings", (), {"price_lookup_max_codes": 2})(),
    )

    response = client.get("/api/stocks/prices", params={"codes": "2330,2317,2454"})

    assert response.status_code == 400
    assert response.json()["detail"] == "A maximum of 2 stock codes may be requested at once"


def test_prices_endpoint_deduplicates_and_trims_codes():
    mock_svc = AsyncMock()
    mock_svc.get_prices.return_value = []
    app.dependency_overrides[get_price_service] = lambda: mock_svc
    try:
        response = client.get("/api/stocks/prices", params={"codes": " 2330,2317,2330, ,2454 "})
    finally:
        app.dependency_overrides.pop(get_price_service, None)

    assert response.status_code == 200
    mock_svc.get_prices.assert_awaited_once()
    codes, stocks = mock_svc.get_prices.await_args.args
    assert codes == ["2330", "2317", "2454"]
    assert stocks == []


def test_create_transaction_uses_live_quote_price(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "date": "2026-01-10",
        "action": "買",
        "code": "2330",
        "name": "台積電",
        "trade_type": "一般",
        "buy_shares": 100,
        "buy_price": 100,
    }
    expected = TransactionRecord(
        id="created",
        date=date(2026, 1, 10),
        action="買",
        code="2330",
        name="台積電",
        trade_type="一般",
        buy_shares=100,
        buy_price=100,
        current_price=123.4,
        expense=10020,
    )
    captured: dict[str, float] = {}

    def fake_append(tx_payload, *, current_price: float = 0.0):
        captured["current_price"] = current_price
        return expected

    monkeypatch.setattr(_test_svc, "append_transaction", fake_append)
    mock_prices = AsyncMock()
    mock_prices.get_price.return_value = type("Quote", (), {"price": 123.4})()
    app.dependency_overrides[get_price_service] = lambda: mock_prices
    try:
        response = client.post("/api/transactions", json=payload)
    finally:
        app.dependency_overrides.pop(get_price_service, None)

    assert response.status_code == 200
    assert captured["current_price"] == pytest.approx(123.4)
    assert response.json()["id"] == "created"


def test_update_transaction_returns_404_when_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(_test_svc, "update_transaction", lambda tx_id, payload: (_ for _ in ()).throw(KeyError(tx_id)))

    response = client.put(
        "/api/transactions/missing",
        json={
            "date": "2026-01-10",
            "action": "買",
            "code": "2330",
            "name": "台積電",
            "trade_type": "一般",
            "buy_shares": 100,
            "buy_price": 100,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_delete_transaction_returns_404_when_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(_test_svc, "delete_transaction", lambda tx_id: (_ for _ in ()).throw(KeyError(tx_id)))

    response = client.delete("/api/transactions/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"


def test_cashflow_crud_endpoints_cover_success_and_not_found(monkeypatch: pytest.MonkeyPatch):
    created = CashflowRecord(
        id="cf-new",
        date=date(2026, 1, 10),
        deposit=5000,
        withdrawal=0,
    )
    updated = CashflowRecord(
        id="cf-existing",
        date=date(2026, 1, 11),
        deposit=0,
        withdrawal=1200,
    )
    monkeypatch.setattr(_test_svc, "read_cashflows", lambda: [created])
    monkeypatch.setattr(_test_svc, "append_cashflow", lambda payload: created)
    monkeypatch.setattr(_test_svc, "update_cashflow", lambda cf_id, payload: updated if cf_id == "cf-existing" else (_ for _ in ()).throw(KeyError(cf_id)))
    monkeypatch.setattr(_test_svc, "delete_cashflow", lambda cf_id: None if cf_id == "cf-existing" else (_ for _ in ()).throw(KeyError(cf_id)))

    list_response = client.get("/api/cashflow")
    create_response = client.post("/api/cashflow", json={"date": "2026-01-10", "deposit": 5000, "withdrawal": 0})
    update_response = client.put("/api/cashflow/cf-existing", json={"date": "2026-01-11", "deposit": 0, "withdrawal": 1200})
    missing_update_response = client.put("/api/cashflow/missing", json={"date": "2026-01-11", "deposit": 0, "withdrawal": 1200})
    delete_response = client.delete("/api/cashflow/cf-existing")
    missing_delete_response = client.delete("/api/cashflow/missing")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == "cf-new"
    assert create_response.status_code == 200
    assert create_response.json()["deposit"] == 5000
    assert update_response.status_code == 200
    assert update_response.json()["withdrawal"] == 1200
    assert missing_update_response.status_code == 404
    assert missing_update_response.json()["detail"] == "Cashflow not found"
    assert delete_response.status_code == 204
    assert missing_delete_response.status_code == 404
    assert missing_delete_response.json()["detail"] == "Cashflow not found"


def test_holdings_endpoint_uses_live_prices(monkeypatch: pytest.MonkeyPatch):
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
        )
    ]
    monkeypatch.setattr(_test_svc, "read_transactions", lambda: txs)
    monkeypatch.setattr(_test_svc, "read_cashflows", lambda: [])
    monkeypatch.setattr(_test_svc, "read_stocks", lambda: [])
    mock_prices = AsyncMock()
    mock_prices.get_prices.return_value = [
        type("Quote", (), {"code": "2330", "price": 150.0})(),
    ]
    app.dependency_overrides[get_price_service] = lambda: mock_prices
    try:
        response = client.get("/api/holdings")
    finally:
        app.dependency_overrides.pop(get_price_service, None)

    assert response.status_code == 200
    assert response.json()[0]["code"] == "2330"
    assert response.json()[0]["current_price"] == pytest.approx(150.0)
