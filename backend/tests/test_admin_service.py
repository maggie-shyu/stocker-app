from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.services.admin_service import AdminService


def test_extract_supabase_usage_metrics_from_prometheus_text():
    metrics = """
# HELP node_filesystem_size_bytes Filesystem size in bytes.
node_filesystem_size_bytes{mountpoint="/var/lib/postgresql/data"} 100
node_filesystem_avail_bytes{mountpoint="/var/lib/postgresql/data"} 25
node_memory_MemTotal_bytes 100
node_memory_MemAvailable_bytes 42
pg_database_size_bytes{datname="postgres"} 536870912
"""

    service = AdminService(client=None)

    assert service._extract_memory_usage_percent(metrics) == 58.0
    assert service._extract_database_space_used_bytes(metrics) == 536870912


def test_extract_supabase_usage_metrics_returns_none_when_missing():
    service = AdminService(client=None)

    assert service._extract_memory_usage_percent("") is None
    assert service._extract_database_space_used_bytes("") is None


def test_read_table_applies_stable_ordering_before_pagination():
    query = MagicMock()
    query.select.return_value = query
    query.order.return_value = query
    query.range.return_value = query
    query.execute.return_value = SimpleNamespace(
        count=2,
        data=[
            {"id": "tx-2", "date": "2025-01-02", "code": "2317"},
            {"id": "tx-1", "date": "2025-01-01", "code": "2330"},
        ],
    )

    client = MagicMock()
    client.table.return_value = query
    service = AdminService(client=client)

    page = service.read_table("transactions", page=2, page_size=25)

    client.table.assert_called_once_with("transactions")
    query.select.assert_called_once_with("*", count="exact")
    query.order.assert_any_call("date", desc=True)
    query.order.assert_any_call("id", desc=True)
    query.range.assert_called_once_with(25, 49)
    assert page.page == 2
    assert page.total == 2
