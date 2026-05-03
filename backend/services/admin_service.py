from __future__ import annotations

import base64
import re
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from backend.models.schemas import (
    AdminOverview,
    AdminTablePage,
    AdminTableSummary,
)
from backend.config import get_settings


class AdminService:
    _TABLES: dict[str, dict[str, Any]] = {
        "transactions": {
            "label": "交易紀錄",
            "description": "All transaction rows across users.",
            "count_column": "id",
            "order_by": [("date", False), ("id", False)],
        },
        "cashflow": {
            "label": "出入金",
            "description": "All cashflow rows across users.",
            "count_column": "id",
            "order_by": [("date", False), ("id", False)],
        },
        "user_settings": {
            "label": "使用者設定",
            "description": "Per-user settings rows.",
            "count_column": "user_id",
            "order_by": [("user_id", True)],
        },
    }

    def __init__(self, client: Any):
        self._db = client

    @staticmethod
    def _count(result: Any) -> int:
        count = getattr(result, "count", None)
        if count is not None:
            return int(count)
        data = getattr(result, "data", None) or []
        return len(data)

    @staticmethod
    def _metric_series(text: str, metric_name: str) -> list[tuple[dict[str, str], float]]:
        series: list[tuple[dict[str, str], float]] = []
        prefix = f"{metric_name}"
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or not line.startswith(prefix):
                continue
            labels: dict[str, str] = {}
            if "{" in line:
                name_and_labels, value_text = line.split("}", 1)
                _, raw_labels = name_and_labels.split("{", 1)
                for key, value in re.findall(r'([a-zA-Z_:][a-zA-Z0-9_:]*)="([^"]*)"', raw_labels):
                    labels[key] = value
            else:
                value_text = line[len(metric_name):]
            try:
                value = float(value_text.strip())
            except ValueError:
                continue
            series.append((labels, value))
        return series

    @staticmethod
    def _metric_value(text: str, metric_name: str, **required_labels: str) -> float | None:
        for labels, value in AdminService._metric_series(text, metric_name):
            if all(labels.get(key) == expected for key, expected in required_labels.items()):
                return value
        return None

    @staticmethod
    def _metric_total(text: str, metric_name: str, **required_labels: str) -> float | None:
        total = 0.0
        found = False
        for labels, value in AdminService._metric_series(text, metric_name):
            if all(labels.get(key) == expected for key, expected in required_labels.items()):
                total += value
                found = True
        return total if found else None

    @staticmethod
    def _metric_total_any(text: str, metric_names: tuple[str, ...], **required_labels: str) -> float | None:
        for metric_name in metric_names:
            total = AdminService._metric_total(text, metric_name, **required_labels)
            if total is not None:
                return total
        return None

    def _project_ref(self) -> str:
        hostname = urlparse(get_settings().supabase_url).hostname or ""
        return hostname.split(".")[0]

    def _fetch_metrics_text(self) -> str | None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_secret_key:
            return None
        project_ref = self._project_ref()
        if not project_ref:
            return None
        credentials = base64.b64encode(
            f"service_role:{settings.supabase_secret_key}".encode("utf-8")
        ).decode("ascii")
        request = Request(
            url=f"https://{project_ref}.supabase.co/customer/v1/privileged/metrics",
            headers={"Authorization": f"Basic {credentials}"},
        )
        try:
            with urlopen(request, timeout=5) as response:
                return response.read().decode("utf-8")
        except (OSError, URLError):
            return None

    def _extract_memory_usage_percent(self, text: str) -> float | None:
        total = self._metric_total_any(
            text,
            ("supabase.node.memory.mem_total_bytes", "node_memory_MemTotal_bytes"),
        )
        available = self._metric_total_any(
            text,
            ("supabase.node.memory.mem_available_bytes", "node_memory_MemAvailable_bytes"),
        )
        if total and available is not None and total > 0:
            return round((1 - (available / total)) * 100, 1)
        return None

    def _extract_cpu_busy_percent(self, text: str) -> float | None:
        # Prefer the richer node exporter snapshot if it is exposed, otherwise
        # fall back to the documented process CPU counter.
        idle = 0.0
        total = 0.0
        for labels, value in self._metric_series(text, "node_cpu_seconds_total"):
            total += value
            if labels.get("mode") == "idle":
                idle += value
        if total > 0:
            return round(100.0 * (1 - idle / total), 1)

        cpu_seconds = self._metric_total_any(
            text,
            ("supabase.process.cpu.seconds.count", "supabase.storage_api.process_cpu.seconds.count"),
        )
        uptime_seconds = self._metric_total_any(
            text,
            ("supabase.process.uptime.seconds", "supabase.storage_api.process.uptime.seconds"),
        )
        if cpu_seconds is not None and uptime_seconds and uptime_seconds > 0:
            # This is a one-core equivalent utilization estimate derived from
            # cumulative CPU time over uptime, because the docs do not expose
            # idle-time counters for the Supabase endpoint.
            return round(100.0 * (cpu_seconds / uptime_seconds), 1)
        return None

    def _extract_disk_usage_percent(self, text: str) -> float | None:
        def pick_series(metric_names: tuple[str, ...]) -> tuple[dict[str, str], float] | None:
            candidates: list[tuple[dict[str, str], float]] = []
            for metric_name in metric_names:
                candidates.extend(self._metric_series(text, metric_name))

            def priority(series: tuple[dict[str, str], float]) -> tuple[int, float]:
                labels, value = series
                fstype = labels.get("fstype", "")
                mountpoint = labels.get("mountpoint", "")
                if fstype and re.fullmatch(r"tmpfs|fuse.*", fstype):
                    return (99, value)
                if mountpoint == "/data":
                    return (0, -value)
                if mountpoint == "/":
                    return (1, -value)
                return (2, -value)

            for labels, value in sorted(candidates, key=priority):
                fstype = labels.get("fstype")
                if fstype and re.fullmatch(r"tmpfs|fuse.*", fstype):
                    continue
                return labels, value
            return None

        size_series = pick_series(("supabase.node.filesystem.size_bytes", "node_filesystem_size_bytes"))
        avail_series = pick_series(("supabase.node.filesystem.available_bytes", "node_filesystem_avail_bytes"))
        if size_series is None or avail_series is None:
            return None

        size_labels, size = size_series
        avail_labels, avail = avail_series
        if size > 0 and {
            key: size_labels.get(key)
            for key in ("device", "mountpoint", "fstype")
        } == {
            key: avail_labels.get(key)
            for key in ("device", "mountpoint", "fstype")
        }:
            return round(100.0 * (1 - (avail / size)), 1)
        return None

    def _extract_connection_rate_percent(self, text: str) -> float | None:
        open_connections = self._metric_total_any(
            text,
            (
                "connection_stats_connection_count",
                "supabase.db.sql.connection_open",
                "pgbouncer_used_clients",
            ),
        )
        max_connections = self._metric_total_any(
            text,
            (
                "max_connections_connection_count",
                "supabase.db.sql.connection_max_open",
                "pgbouncer_config_max_client_connections",
            ),
        )
        if open_connections is not None and max_connections is not None and max_connections > 0:
            return round(100.0 * (open_connections / max_connections), 1)
        return None

    def _extract_active_queries(self, text: str) -> int | None:
        active_queries = self._metric_total_any(
            text,
            (
                "supabase.pg_stat_database.num_backends",
                "pgbouncer_pools_client_active_connections",
            ),
        )
        if active_queries is not None:
            return int(round(active_queries))
        return None

    def _supabase_usage_metrics(self) -> dict[str, float | int | None]:
        text = self._fetch_metrics_text()
        if not text:
            return {
                "supabase_memory_usage_percent": None,
                "cpu_busy_percent": None,
                "disk_usage_percent": None,
                "connection_rate_percent": None,
                "active_queries": None,
            }
        return {
            "supabase_memory_usage_percent": self._extract_memory_usage_percent(text),
            "cpu_busy_percent": self._extract_cpu_busy_percent(text),
            "disk_usage_percent": self._extract_disk_usage_percent(text),
            "connection_rate_percent": self._extract_connection_rate_percent(text),
            "active_queries": self._extract_active_queries(text),
        }

    def _count_rows(self, table_name: str, count_column: str = "id") -> int:
        result = (
            self._db.table(table_name)
            .select(count_column, count="exact")
            .limit(1)
            .execute()
        )
        return self._count(result)

    def _count_distinct_users(self, table_name: str) -> int:
        rows = (
            self._db.table(table_name)
            .select("user_id")
            .execute()
            .data
        )
        return len({row["user_id"] for row in rows if row.get("user_id")})

    def get_overview(self) -> AdminOverview:
        metrics = self._supabase_usage_metrics()
        return AdminOverview(
            total_users=self._count_rows("user_settings", "user_id"),
            users_with_transactions=self._count_distinct_users("transactions"),
            users_with_cashflows=self._count_distinct_users("cashflow"),
            supabase_memory_usage_percent=metrics["supabase_memory_usage_percent"],
            cpu_busy_percent=metrics["cpu_busy_percent"],
            disk_usage_percent=metrics["disk_usage_percent"],
            connection_rate_percent=metrics["connection_rate_percent"],
            active_queries=metrics["active_queries"],
        )

    def list_tables(self) -> list[AdminTableSummary]:
        summaries: list[AdminTableSummary] = []
        for table_name, metadata in self._TABLES.items():
            summaries.append(
                AdminTableSummary(
                    name=table_name,
                    label=metadata["label"],
                    description=metadata["description"],
                    row_count=self._count_rows(table_name, metadata["count_column"]),
                )
            )
        return summaries

    def read_table(self, table_name: str, *, page: int, page_size: int) -> AdminTablePage:
        metadata = self._TABLES.get(table_name)
        if metadata is None:
            raise KeyError(table_name)
        start = (page - 1) * page_size
        end = start + page_size - 1
        query = self._db.table(table_name).select("*", count="exact")
        for column, ascending in metadata["order_by"]:
            query = query.order(column, desc=not ascending)
        result = query.range(start, end).execute()
        items = result.data or []
        columns = list(items[0].keys()) if items else []
        return AdminTablePage(
            table_name=table_name,
            label=metadata["label"],
            page=page,
            page_size=page_size,
            total=self._count(result),
            columns=columns,
            items=items,
        )
