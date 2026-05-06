from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.infrastructure.supabase.admin_store import SupabaseAdminStore


def test_count_prefers_result_count_when_available():
    assert SupabaseAdminStore._count(SimpleNamespace(count=7, data=[1, 2])) == 7


def test_count_rows_uses_exact_count_query():
    query = MagicMock()
    query.select.return_value = query
    query.limit.return_value = query
    query.execute.return_value = SimpleNamespace(count=5, data=[])
    client = MagicMock()
    client.table.return_value = query

    store = SupabaseAdminStore(client)
    result = store.count_rows("transactions", "id")

    assert result == 5
    client.table.assert_called_once_with("transactions")
    query.select.assert_called_once_with("id", count="exact")
    query.limit.assert_called_once_with(1)


def test_count_distinct_users_deduplicates_and_ignores_missing_ids():
    query = MagicMock()
    query.select.return_value.execute.return_value.data = [
        {"user_id": "user-1"},
        {"user_id": "user-2"},
        {"user_id": "user-1"},
        {"user_id": None},
        {},
    ]
    client = MagicMock()
    client.table.return_value = query

    store = SupabaseAdminStore(client)

    assert store.count_distinct_users("transactions") == 2


def test_read_table_page_applies_ordering_and_range():
    query = MagicMock()
    query.select.return_value = query
    query.order.return_value = query
    query.range.return_value = query
    query.execute.return_value = SimpleNamespace(
        count=3,
        data=[{"id": "tx-3"}, {"id": "tx-2"}],
    )
    client = MagicMock()
    client.table.return_value = query

    store = SupabaseAdminStore(client)
    total, items = store.read_table_page(
        "transactions",
        page=2,
        page_size=2,
        order_by=[("date", False), ("id", False)],
    )

    assert total == 3
    assert items == [{"id": "tx-3"}, {"id": "tx-2"}]
    query.order.assert_any_call("date", desc=True)
    query.order.assert_any_call("id", desc=True)
    query.range.assert_called_once_with(2, 3)
