from unittest.mock import ANY, MagicMock, patch
from datetime import date
from types import SimpleNamespace

import pytest
from postgrest.exceptions import APIError

from backend.infrastructure.supabase.ledger_store import SupabaseLedgerStore
from backend.models.api.ledger import CashflowCreate, FeedbackCreate, TransactionCreate
from backend.models.domain.ledger import CashflowRecord, UserSettings


USER_ID = "user-123"
TX_UUID = "tx-uuid-1"
CF_UUID = "cf-uuid-1"
FEEDBACK_UUID = "feedback-uuid-1"
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
    assert settings.cash_dividend_transfer_fee == 10.0


def test_get_settings_falls_back_when_cash_dividend_fee_column_is_missing(client):
    table = MagicMock()
    client.table.return_value = table
    table.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = [
        APIError({"message": "column user_settings.cash_dividend_transfer_fee does not exist", "code": "42703"}),
        SimpleNamespace(
            data={
                "commission_discount_rate": 0.6,
                "base_commission_rate": 0.001425,
                "minimum_fee": 20.0,
                "odd_lot_minimum_fee": 1.0,
                "stock_tax_rate": 0.003,
                "day_trade_tax_rate": 0.0015,
                "etf_tax_rate": 0.001,
                "bond_etf_tax_rate": 0.0,
            }
        ),
    ]
    svc = make_service(client)

    settings = svc.get_settings()

    assert settings.cash_dividend_transfer_fee == 10.0
    assert table.select.call_args_list[1].args[0] == svc._legacy_settings_columns


def test_update_settings_upserts_row(client):
    table = MagicMock()
    client.table.return_value = table
    svc = make_service(client)

    settings = UserSettings(commission_discount_rate=0.6)
    result = svc.update_settings(settings)

    table.upsert.assert_called_once()
    assert result.commission_discount_rate == 0.6


def test_update_settings_falls_back_when_cash_dividend_fee_column_is_missing(client):
    table = MagicMock()
    client.table.return_value = table
    table.upsert.return_value.execute.side_effect = [
        APIError({"message": "column user_settings.cash_dividend_transfer_fee does not exist", "code": "42703"}),
        SimpleNamespace(data=[]),
    ]
    svc = make_service(client)

    result = svc.update_settings(UserSettings(commission_discount_rate=0.6, cash_dividend_transfer_fee=10))

    assert result.cash_dividend_transfer_fee == 10.0
    legacy_payload = table.upsert.call_args_list[1].args[0]
    assert "cash_dividend_transfer_fee" not in legacy_payload


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
    inserted_row = table.insert.call_args.args[0]
    assert "dividend_income" not in inserted_row


def test_append_dividend_transaction_uses_shares_and_price(client):
    table = MagicMock()
    client.table.return_value = table
    table.insert.return_value.execute.return_value.data = [
        {
            "id": TX_UUID,
            "date": "2025-08-06",
            "action": "股利",
            "code": "3130",
            "name": "一零四",
            "trade_type": "一般",
            "buy_shares": None,
            "buy_price": None,
            "sell_shares": None,
            "sell_price": None,
            "dividend_shares": 100.0,
            "dividend_price": 2.0,
            "reason": None,
        }
    ]
    svc = make_service(client)

    result = svc.append_transaction(
        TransactionCreate(
            date=date(2025, 8, 6),
            action="股利",
            code="3130",
            name="一零四",
            trade_type="一般",
            dividend_shares=100,
            dividend_price=2,
        ),
        UserSettings(commission_discount_rate=0.6),
    )

    assert result.income == pytest.approx(190)
    inserted_row = table.insert.call_args.args[0]
    assert inserted_row["dividend_shares"] == 100
    assert inserted_row["dividend_price"] == 2
    assert "dividend_income" not in inserted_row


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
            dividend_shares=100,
            dividend_price=2,
        ),
    ]

    assert svc.replace_transactions(payloads) == 2
    table.insert.assert_called_once()
    inserted_rows = table.insert.call_args.args[0]
    assert inserted_rows[1]["dividend_shares"] == 100
    assert inserted_rows[1]["dividend_price"] == 2


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


def test_read_feedbacks_returns_user_rows(client):
    stub_read_chain(
        client,
        [
            {
                "id": FEEDBACK_UUID,
                "subject": "儀表板資訊",
                "body": "希望可以看到更多儀表板資訊",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        ],
    )
    svc = make_service(client)

    result = svc.read_feedbacks()

    assert result[0].id == FEEDBACK_UUID
    assert result[0].subject == "儀表板資訊"
    assert result[0].body == "希望可以看到更多儀表板資訊"


def test_append_feedback_inserts_content_for_user(client):
    table = MagicMock()
    client.table.return_value = table
    table.insert.return_value.execute.return_value.data = [
        {
            "id": FEEDBACK_UUID,
            "subject": "技術分析",
            "body": "想加上技術分析",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    ]
    svc = make_service(client)

    result = svc.append_feedback(FeedbackCreate(subject="技術分析", body="想加上技術分析"))

    table.insert.assert_called_once_with({"user_id": USER_ID, "subject": "技術分析", "body": "想加上技術分析"})
    assert result.subject == "技術分析"
    assert result.body == "想加上技術分析"


def test_update_feedback_scopes_update_to_user(client):
    table = MagicMock()
    client.table.return_value = table
    table.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": FEEDBACK_UUID,
            "subject": "更新主旨",
            "body": "更新後的建議",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-02T00:00:00+00:00",
        }
    ]
    svc = make_service(client)

    result = svc.update_feedback(FEEDBACK_UUID, FeedbackCreate(subject="更新主旨", body="更新後的建議"))

    assert result.subject == "更新主旨"
    assert result.body == "更新後的建議"
    table.update.assert_called_once_with({"subject": "更新主旨", "body": "更新後的建議", "updated_at": ANY})


def test_delete_feedback_raises_key_error_when_row_missing(client):
    table = MagicMock()
    client.table.return_value = table
    table.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    svc = make_service(client)

    with pytest.raises(KeyError):
        svc.delete_feedback(FEEDBACK_UUID)
