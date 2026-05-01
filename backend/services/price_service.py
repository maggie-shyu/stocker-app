from __future__ import annotations

import asyncio
import time

import httpx

from models.schemas import PriceQuote, StockLookup


class PriceService:
    def __init__(self):
        self._cache: dict[str, tuple[float, PriceQuote]] = {}

    async def get_prices(self, codes: list[str], stocks: list[StockLookup]) -> list[PriceQuote]:
        stock_names = {stock.code: stock.name for stock in stocks}
        tasks = [self.get_price(code.strip(), stock_names.get(code.strip())) for code in codes if code.strip()]
        return await asyncio.gather(*tasks) if tasks else []

    async def get_price(self, code: str, name: str | None = None) -> PriceQuote:
        cached = self._cache.get(code)
        if cached and cached[0] > time.monotonic():
            return cached[1]

        for market in ("tse", "otc"):
            quote = await self._fetch_market_price(code, market, name)
            if quote.price is not None:
                self._cache[code] = (time.monotonic() + 1, quote)
                return quote

        quote = PriceQuote(code=code, name=name, price=None, delayed=True)
        self._cache[code] = (time.monotonic() + 1, quote)
        return quote

    async def _fetch_market_price(self, code: str, market: str, name: str | None) -> PriceQuote:
        url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
        params = {"ex_ch": f"{market}_{code}.tw", "json": "1", "delay": "0"}
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception:
            return PriceQuote(code=code, name=name, price=None, delayed=True)

        items = data.get("msgArray") or []
        if not items:
            return PriceQuote(code=code, name=name, price=None, delayed=True)
        raw = items[0]
        price = raw.get("z")
        if price in (None, "", "-"):
            price = raw.get("y")
        try:
            numeric_price = float(price)
        except (TypeError, ValueError):
            numeric_price = None
        return PriceQuote(
            code=code,
            name=raw.get("n") or name,
            price=numeric_price,
            delayed=numeric_price is None,
            source=f"twse:{market}",
        )
