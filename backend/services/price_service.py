from __future__ import annotations

import asyncio
import time

import httpx
import yfinance as yf
from datetime import timedelta, date

from backend.models.schemas import PriceQuote, StockLookup


class PriceService:
    def __init__(self):
        self._cache: dict[str, tuple[float, PriceQuote]] = {}
        self._semaphore = asyncio.Semaphore(10)

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
            async with self._semaphore:
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
        prev = raw.get("y")
        if price in (None, "", "-"):
            price = prev
        try:
            numeric_price = float(price)
        except (TypeError, ValueError):
            numeric_price = None
            
        try:
            numeric_prev = float(prev)
        except (TypeError, ValueError):
            numeric_prev = None

        return PriceQuote(
            code=code,
            name=raw.get("n") or name,
            price=numeric_price,
            previous_close=numeric_prev,
            delayed=numeric_price is None,
            source=f"twse:{market}",
        )

    async def get_benchmark_return_rate(self, ticker: str, start_date: date) -> float | None:
        today = date.today()
        if start_date > today:
            return None

        def fetch():
            try:
                df = yf.Ticker(ticker).history(start=start_date - timedelta(days=7), end=today + timedelta(days=2))
                if df.empty:
                    return None
                df_after_start = df[df.index.date >= start_date]
                if not df_after_start.empty:
                    start_adj_close = float(df_after_start["Close"].iloc[0])
                else:
                    start_adj_close = float(df["Close"].iloc[-1])
                
                current_adj_close = float(df["Close"].iloc[-1])
                if start_adj_close and start_adj_close > 0:
                    return (current_adj_close - start_adj_close) / start_adj_close
                return None
            except Exception as e:
                print(f"Error fetching {ticker} benchmark: {e}")
                return None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fetch)
