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
        rows = self._db.table("stocks").select("code, name").execute().data
        self._stock_cache = [
            StockLookup(code=row["code"], name=row["name"])
            for row in rows
        ]
        return self._stock_cache

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
