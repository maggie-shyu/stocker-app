from unittest.mock import MagicMock, patch
from datetime import date

import pytest

from backend.infrastructure.supabase.ledger_store import SupabaseLedgerStore
from backend.models.api.ledger import CashflowCreate, TransactionCreate
from backend.models.domain.ledger import CashflowRecord, UserSettings


USER_ID = "user-123"
TX_UUID = "tx-uuid-1"
CF_UUID = "cf-uuid-1"
TEST_SETTINGS = UserSettings(commission_discount_rate=1.0)


def make_service(mock_client):
    return SupabaseLedgerStore(mock_client, USER_ID)


def stub_read_chain(mock_client, data):
    table = MagicMock()
    mock_client.table.return_value = table
    table.select.return_value.eq.return_value.order.return_value.execute.return_value.data = data
    return table


@pytest.fixture
def client():
    return MagicMock()


def test_read_transactions_empty(client):
    stub_read_chain(client, [])
    svc = make_service(client)
    assert svc.read_transactions(TEST_SETTINGS) == []


def test_read_transactions_returns_records(client):
    stub_read_chain(
        client,
        [
            {
                "id": TX_UUID,
                "date": "2025-08-06",
                "action": "買",
                "code": "3130",
                "name": "一零四",
                "trade_type": "一般",
                "buy_shares": 1000.0,
                "buy_price": 224.5,
                "sell_shares": None,
                "sell_price": None,
                "dividend_income": None,
                "reason": None,
            }
        ],
    )
    svc = make_service(client)
    result = svc.read_transactions(TEST_SETTINGS)
    assert len(result) == 1
    assert result[0].id == TX_UUID
    assert result[0].code == "3130"
    assert result[0].action == "買"


def test_read_transactions_uses_stored_settings_when_not_passed(client):
    stub_read_chain(
        client,
        [
            {
                "id": TX_UUID,
                "date": "2025-08-06",
                "action": "買",
                "code": "3130",
                "name": "一零四",
                "trade_type": "一般",
                "buy_shares": 1000.0,
                "buy_price": 224.5,
                "sell_shares": None,
                "sell_price": None,
                "dividend_income": None,
                "reason": None,
            }
        ],
    )
    svc = make_service(client)
    with patch.object(svc, "get_settings", return_value=UserSettings(commission_discount_rate=0.6)) as get_settings:
        result = svc.read_transactions()

    assert len(result) == 1
    assert result[0].discount_rate == pytest.approx(0.6)
    get_settings.assert_called_once()


def test_delete_transaction_raises_key_error_when_not_found(client):
    table = MagicMock()
    client.table.return_value = table
    table.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    svc = make_service(client)
    with pytest.raises(KeyError):
        svc.delete_transaction("nonexistent-id")


def test_read_cashflows_returns_plain_rows(client):
    stub_read_chain(
        client,
        [
            {
                "id": CF_UUID,
                "date": "2025-01-01",
                "deposit": 100000.0,
                "withdrawal": 0.0,
            },
            {
                "id": "cf-2",
                "date": "2025-02-01",
                "deposit": 50000.0,
                "withdrawal": 0.0,
            },
        ],
    )
    svc = make_service(client)
    result = svc.read_cashflows()
    assert result[0].deposit == 100000.0
    assert result[1].withdrawal == 0.0


def test_get_settings_returns_defaults_when_missing(client):
    table = MagicMock()
    client.table.return_value = table
    table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    svc = make_service(client)
    settings = svc.get_settings()
    assert settings.commission_discount_rate == 1.0


def test_get_settings_returns_stored_values(client):
    table = MagicMock()
    client.table.return_value = table
    table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "commission_discount_rate": 0.6,
        "base_commission_rate": 0.001425,
        "minimum_fee": 20.0,
        "odd_lot_minimum_fee": 1.0,
        "stock_tax_rate": 0.003,
        "day_trade_tax_rate": 0.0015,
        "etf_tax_rate": 0.001,
        "bond_etf_tax_rate": 0.0,
    }
    svc = make_service(client)
    settings = svc.get_settings()
    assert settings.commission_discount_rate == 0.6
    assert settings.etf_tax_rate == 0.001


def test_update_settings_upserts_row(client):
    table = MagicMock()
    client.table.return_value = table
    svc = make_service(client)

    settings = UserSettings(commission_discount_rate=0.6)
    result = svc.update_settings(settings)

    table.upsert.assert_called_once()
    assert result.commission_discount_rate == 0.6


def test_append_transaction_builds_record_with_current_price(client):
    table = MagicMock()
    client.table.return_value = table
    table.insert.return_value.execute.return_value.data = [
        {
            "id": TX_UUID,
            "date": "2025-08-06",
            "action": "買",
            "code": "3130",
            "name": "一零四",
            "trade_type": "一般",
            "buy_shares": 1000.0,
            "buy_price": 224.5,
            "sell_shares": None,
            "sell_price": None,
            "dividend_income": None,
            "reason": None,
        }
    ]
    svc = make_service(client)
    result = svc.append_transaction(
        TransactionCreate(
            date=date(2025, 8, 6),
            action="買",
            code="3130",
            name="一零四",
            trade_type="一般",
            buy_shares=1000,
            buy_price=224.5,
        ),
        UserSettings(commission_discount_rate=0.6),
        current_price=250.0,
    )

    assert result.id == TX_UUID
    assert result.current_price == pytest.approx(250.0)
    assert result.discount_rate == pytest.approx(0.6)


def test_replace_transactions_returns_zero_for_empty_payloads(client):
    svc = make_service(client)

    assert svc.replace_transactions([]) == 0


def test_replace_transactions_inserts_all_payloads(client):
    table = MagicMock()
    client.table.return_value = table
    svc = make_service(client)

    payloads = [
        TransactionCreate(
            date=date(2025, 1, 1),
            action="買",
            code="2330",
            name="台積電",
            trade_type="一般",
            buy_shares=100,
            buy_price=100,
        ),
        TransactionCreate(
            date=date(2025, 1, 2),
            action="股利",
            code="2330",
            name="台積電",
            trade_type="一般",
            dividend_income=200,
        ),
    ]

    assert svc.replace_transactions(payloads) == 2
    table.insert.assert_called_once()


def test_update_transaction_returns_updated_record(client):
    table = MagicMock()
    client.table.return_value = table
    table.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": TX_UUID,
            "date": "2025-08-07",
            "action": "賣",
            "code": "3130",
            "name": "一零四",
            "trade_type": "一般",
            "buy_shares": None,
            "buy_price": None,
            "sell_shares": 1000.0,
            "sell_price": 250.0,
            "dividend_income": None,
            "reason": "調節",
        }
    ]
    svc = make_service(client)
    result = svc.update_transaction(
        TX_UUID,
        TransactionCreate(
            date=date(2025, 8, 7),
            action="賣",
            code="3130",
            name="一零四",
            trade_type="一般",
            sell_shares=1000,
            sell_price=250,
            reason="調節",
        ),
        TEST_SETTINGS,
    )

    assert result.action == "賣"
    assert result.reason == "調節"


def test_append_cashflow_returns_record(client):
    table = MagicMock()
    client.table.return_value = table
    table.insert.return_value.execute.return_value.data = [
        {"id": CF_UUID, "date": "2025-01-01", "deposit": 100000.0, "withdrawal": 0.0}
    ]
    svc = make_service(client)

    result = svc.append_cashflow(
        CashflowCreate(date=date(2025, 1, 1), deposit=100000, withdrawal=0)
    )

    assert result.id == CF_UUID
    assert result.deposit == pytest.approx(100000.0)


def test_replace_cashflows_returns_zero_for_empty_payloads(client):
    svc = make_service(client)

    assert svc.replace_cashflows([]) == 0


def test_update_cashflow_returns_updated_record(client):
    table = MagicMock()
    client.table.return_value = table
    table.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": CF_UUID, "date": "2025-02-01", "deposit": 50000.0, "withdrawal": 0.0}
    ]
    svc = make_service(client)
    result = svc.update_cashflow(
        CF_UUID,
        CashflowCreate(date=date(2025, 2, 1), deposit=50000, withdrawal=0),
    )

    assert result.id == CF_UUID
    assert result.deposit == pytest.approx(50000.0)


def test_update_cashflow_raises_key_error_when_row_missing(client):
    table = MagicMock()
    client.table.return_value = table
    table.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    svc = make_service(client)
    with pytest.raises(KeyError):
        svc.update_cashflow(
            CF_UUID,
            CashflowCreate(date=date(2025, 2, 1), deposit=50000, withdrawal=0),
        )
