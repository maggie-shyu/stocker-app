from unittest.mock import MagicMock, patch
from datetime import date

import pytest

from backend.models.schemas import CashflowCreate, CashflowRecord, TransactionCreate
from backend.services.supabase_service import SupabaseService


USER_ID = "user-123"
TX_UUID = "tx-uuid-1"
CF_UUID = "cf-uuid-1"


def make_service(mock_client):
    return SupabaseService(mock_client, USER_ID)


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
    with patch.object(svc, "get_commission_discount_rate", return_value=0.0):
        assert svc.read_transactions() == []


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
    with patch.object(svc, "get_commission_discount_rate", return_value=0.0):
        result = svc.read_transactions()
    assert len(result) == 1
    assert result[0].id == TX_UUID
    assert result[0].code == "3130"
    assert result[0].action == "買"


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


def test_get_commission_discount_rate_returns_default_when_missing(client):
    table = MagicMock()
    client.table.return_value = table
    table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    svc = make_service(client)
    assert svc.get_commission_discount_rate() == 1.0


def test_get_commission_discount_rate_returns_stored_value(client):
    table = MagicMock()
    client.table.return_value = table
    table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "commission_discount_rate": 0.6
    }
    svc = make_service(client)
    assert svc.get_commission_discount_rate() == 0.6


def test_set_commission_discount_rate_upserts_row(client):
    table = MagicMock()
    client.table.return_value = table
    svc = make_service(client)

    result = svc.set_commission_discount_rate(0.6)

    table.upsert.assert_called_once_with(
        {
            "user_id": USER_ID,
            "commission_discount_rate": 0.6,
        }
    )
    assert result == 0.6


def test_search_stocks_filters_by_query(client):
    table = MagicMock()
    client.table.return_value = table
    table.select.return_value.execute.return_value.data = [
        {"code": "0050", "name": "元大台灣50"},
        {"code": "0051", "name": "元大中型100"},
    ]
    svc = make_service(client)
    result = svc.search_stocks("0050")
    assert len(result) == 1
    assert result[0].code == "0050"


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

    with patch.object(svc, "get_commission_discount_rate", return_value=0.6):
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

    with patch.object(svc, "get_commission_discount_rate", return_value=0.0):
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


def test_update_cashflow_returns_matching_row_from_readback(client):
    table = MagicMock()
    client.table.return_value = table
    table.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": CF_UUID}
    ]
    svc = make_service(client)
    with patch.object(
        svc,
        "read_cashflows",
        return_value=[
            CashflowRecord(id="other", date=date(2025, 1, 1), deposit=100000, withdrawal=0),
            CashflowRecord(id=CF_UUID, date=date(2025, 2, 1), deposit=50000, withdrawal=0),
        ],
    ):
        result = svc.update_cashflow(
            CF_UUID,
            CashflowCreate(date=date(2025, 2, 1), deposit=50000, withdrawal=0),
        )

    assert result.id == CF_UUID
    assert result.deposit == pytest.approx(50000.0)


def test_update_cashflow_raises_key_error_when_readback_missing(client):
    table = MagicMock()
    client.table.return_value = table
    table.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": CF_UUID}
    ]
    svc = make_service(client)
    with patch.object(svc, "read_cashflows", return_value=[]):
        with pytest.raises(KeyError):
            svc.update_cashflow(
                CF_UUID,
                CashflowCreate(date=date(2025, 2, 1), deposit=50000, withdrawal=0),
            )


def test_read_stocks_uses_cache_after_first_query(client):
    table = MagicMock()
    client.table.return_value = table
    table.select.return_value.execute.return_value.data = [
        {"code": "0050", "name": "元大台灣50"}
    ]
    svc = make_service(client)

    first = svc.read_stocks()
    second = svc.read_stocks()

    assert first[0].code == "0050"
    assert second[0].name == "元大台灣50"
    client.table.assert_called_once_with("stocks")


def test_search_stocks_returns_ranked_prefix_matches_and_limit(client):
    svc = make_service(client)
    with patch.object(
        svc,
        "read_stocks",
        return_value=[
            type("Stock", (), {"code": "0050", "name": "元大台灣50"})(),
            type("Stock", (), {"code": "0056", "name": "元大高股息"})(),
            type("Stock", (), {"code": "1101", "name": "台泥"})(),
        ],
    ):
        result = svc.search_stocks("00", limit=2)

    assert [stock.code for stock in result] == ["0050", "0056"]
