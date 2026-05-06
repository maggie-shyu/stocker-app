from __future__ import annotations

from typing import Any


class SupabaseAdminStore:
    def __init__(self, client: Any):
        self._db = client

    @staticmethod
    def _count(result: Any) -> int:
        count = getattr(result, "count", None)
        if count is not None:
            return int(count)
        data = getattr(result, "data", None) or []
        return len(data)

    def count_rows(self, table_name: str, count_column: str = "id") -> int:
        result = (
            self._db.table(table_name)
            .select(count_column, count="exact")
            .limit(1)
            .execute()
        )
        return self._count(result)

    def count_distinct_users(self, table_name: str) -> int:
        rows = self._db.table(table_name).select("user_id").execute().data
        return len({row["user_id"] for row in rows if row.get("user_id")})

    def read_table_page(
        self,
        table_name: str,
        *,
        page: int,
        page_size: int,
        order_by: list[tuple[str, bool]],
    ) -> tuple[int, list[dict[str, Any]]]:
        start = (page - 1) * page_size
        end = start + page_size - 1
        query = self._db.table(table_name).select("*", count="exact")
        for column, ascending in order_by:
            query = query.order(column, desc=not ascending)
        result = query.range(start, end).execute()
        return self._count(result), result.data or []
