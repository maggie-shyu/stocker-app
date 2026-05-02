from unittest.mock import MagicMock, patch

import pytest

from services.supabase_service import SupabaseService


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
