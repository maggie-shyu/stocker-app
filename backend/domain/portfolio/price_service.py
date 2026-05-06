from __future__ import annotations

import asyncio
import time
from datetime import date

from backend.infrastructure.market_data.yfinance_quote_provider import YfinanceQuoteProvider
from backend.models.domain.portfolio import PriceQuote, StockLookup


class PriceService:
    def __init__(self, quote_provider: YfinanceQuoteProvider | None = None):
        self._cache: dict[str, tuple[float, PriceQuote]] = {}
        self._TTL = 60  # seconds
        self._quote_provider = quote_provider or YfinanceQuoteProvider()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_prices(self, codes: list[str], stocks: list[StockLookup]) -> list[PriceQuote]:
        codes = [c.strip() for c in codes if c.strip()]
        if not codes:
            return []
        stock_names = {stock.code: stock.name for stock in stocks}

        now = time.monotonic()
        missing = [c for c in codes if c not in self._cache or self._cache[c][0] <= now]

        if missing:
            await self._fetch_batch(missing, stock_names)

        return [self._cache[c][1] if c in self._cache else PriceQuote(code=c, name=stock_names.get(c), price=None, delayed=True)
                for c in codes]

    async def get_price(self, code: str, name: str | None = None) -> PriceQuote:
        results = await self.get_prices([code], [StockLookup(code=code, name=name or "")])
        return results[0]

    # ------------------------------------------------------------------
    # Batch fetch via yfinance (works from any IP)
    # ------------------------------------------------------------------

    async def _fetch_batch(self, codes: list[str], stock_names: dict[str, str]) -> None:
        loop = asyncio.get_event_loop()
        quotes = await loop.run_in_executor(None, self._quote_provider.fetch_quotes, codes, stock_names)
        expire = time.monotonic() + self._TTL
        for q in quotes:
            self._cache[q.code] = (expire, q)

    # ------------------------------------------------------------------
    # Benchmark return rate (unchanged)
    # ------------------------------------------------------------------

    async def get_benchmark_return_rate(self, ticker: str, start_date: date) -> float | None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._quote_provider.get_benchmark_return_rate,
            ticker,
            start_date,
        )
