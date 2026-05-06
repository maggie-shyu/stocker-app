from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.admin.metrics import AdminService


def test_extract_supabase_usage_metrics_from_prometheus_text():
    metrics = """
# HELP supabase.node.filesystem.size_bytes Filesystem size in bytes.
supabase.node.filesystem.size_bytes{fstype="ext4",mountpoint="/data"} 100
supabase.node.filesystem.available_bytes{fstype="ext4",mountpoint="/data"} 25
supabase.node.filesystem.size_bytes{fstype="ext4",mountpoint="/"} 999
supabase.node.filesystem.available_bytes{fstype="ext4",mountpoint="/"} 888
supabase.node.filesystem.size_bytes{fstype="tmpfs",mountpoint="/run"} 999
supabase.node.filesystem.available_bytes{fstype="tmpfs",mountpoint="/run"} 888
supabase.node.memory.mem_total_bytes 100
supabase.node.memory.mem_available_bytes 42
supabase.db.sql.connection_open 7
supabase.db.sql.connection_max_open 10
supabase.pg_stat_database.num_backends 12
"""

    service = AdminService(client=None)

    assert service._extract_memory_usage_percent(metrics) == 58.0
    assert service._extract_disk_usage_percent(metrics) == 75.0
    assert service._extract_connection_rate_percent(metrics) == 70.0
    assert service._extract_active_queries(metrics) == 12


def test_extract_disk_usage_prefers_data_mount_when_available():
    metrics = """
supabase.node.filesystem.size_bytes{fstype="ext4",mountpoint="/"} 10359754752
supabase.node.filesystem.available_bytes{fstype="ext4",mountpoint="/"} 3050774528
supabase.node.filesystem.size_bytes{fstype="ext4",mountpoint="/data"} 2077073408
supabase.node.filesystem.available_bytes{fstype="ext4",mountpoint="/data"} 1711267840
"""

    service = AdminService(client=None)

    assert service._extract_disk_usage_percent(metrics) == 17.6


def test_extract_supabase_usage_metrics_falls_back_to_pgbouncer_metrics():
    metrics = """
supabase.node.memory.mem_total_bytes 100
supabase.node.memory.mem_available_bytes 42
pgbouncer_used_clients 1
pgbouncer_config_max_client_connections 200
pgbouncer_pools_client_active_connections{supabase_project_ref="abc",supabase_identifier="abc",service_type="db",database="pgbouncer",user="pgbouncer"} 4
"""

    service = AdminService(client=None)

    assert service._extract_memory_usage_percent(metrics) == 58.0
    assert service._extract_connection_rate_percent(metrics) == 0.5
    assert service._extract_active_queries(metrics) == 4


def test_extract_connection_rate_prefers_connection_stats_metrics():
    metrics = """
connection_stats_connection_count{supabase_project_ref="abc",supabase_identifier="abc",service_type="postgresql",server="localhost:5432",username="authenticator"} 4
connection_stats_connection_count{supabase_project_ref="abc",supabase_identifier="abc",service_type="postgresql",server="localhost:5432",username="other"} 4
max_connections_connection_count{supabase_project_ref="abc",supabase_identifier="abc",service_type="postgresql",server="localhost:5432"} 60
"""

    service = AdminService(client=None)

    assert service._extract_connection_rate_percent(metrics) == 13.3


def test_extract_supabase_usage_metrics_returns_none_when_missing():
    service = AdminService(client=None)

    assert service._extract_memory_usage_percent("") is None
    assert service._extract_disk_usage_percent("") is None
    assert service._extract_connection_rate_percent("") is None
    assert service._extract_active_queries("") is None


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
