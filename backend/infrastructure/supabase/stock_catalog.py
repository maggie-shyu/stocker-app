from __future__ import annotations

from typing import Any

from backend.models.domain.portfolio import StockLookup


class SupabaseStockCatalog:
    def __init__(self, client: Any):
        self._db = client
        self._stock_cache: list[StockLookup] | None = None

    def read_stocks(self) -> list[StockLookup]:
        if self._stock_cache is not None:
            return self._stock_cache
        # PostgREST caps each response at 1000 rows; page with range() until exhausted
        rows: list[dict] = []
        page, size = 0, 1000
        while True:
            batch = (
                self._db.table("stocks")
                .select("code, name")
                .order("code")
                .range(page * size, page * size + size - 1)
                .execute()
                .data
            )
            rows.extend(batch)
            if len(batch) < size:
                break
            page += 1
        self._stock_cache = [
            StockLookup(code=row["code"], name=row["name"])
            for row in rows
        ]
        return self._stock_cache

    def upsert_stock(self, code: str, name: str) -> None:
        self._db.table("stocks").upsert({"code": code, "name": name}, on_conflict="code").execute()
        # Invalidate cache so the new stock is visible in future searches
        self._stock_cache = None

    def search_stocks(self, query: str, *, limit: int = 20) -> list[StockLookup]:
        normalized = query.strip().lower()
        all_stocks = self.read_stocks()
        if not normalized:
            return all_stocks[:limit]

        def score(stock: StockLookup) -> tuple[int, str]:
            code = stock.code.lower()
            name = stock.name.lower()
            if code == normalized or name == normalized:
                return (0, code)
            if code.startswith(normalized) or name.startswith(normalized):
                return (1, code)
            return (2, code)

        matches = [
            stock
            for stock in all_stocks
            if normalized in stock.code.lower() or normalized in stock.name.lower()
        ]
        return sorted(matches, key=score)[:limit]
