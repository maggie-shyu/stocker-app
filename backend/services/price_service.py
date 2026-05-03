from __future__ import annotations

import asyncio
import time
from datetime import timedelta, date

import yfinance as yf

from backend.models.schemas import PriceQuote, StockLookup


class PriceService:
    def __init__(self):
        self._cache: dict[str, tuple[float, PriceQuote]] = {}
        self._TTL = 60  # seconds

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
        quotes = await loop.run_in_executor(None, self._yf_batch, codes, stock_names)
        expire = time.monotonic() + self._TTL
        for q in quotes:
            self._cache[q.code] = (expire, q)

    def _yf_batch(self, codes: list[str], stock_names: dict[str, str]) -> list[PriceQuote]:
        tickers_tw = [f"{c}.TW" for c in codes]
        tickers_two = [f"{c}.TWO" for c in codes]
        tickers = tickers_tw + tickers_two
        try:
            # Download last 2 trading days so we always have previous close
            df = yf.download(
                " ".join(tickers),
                period="2d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as e:
            print(f"[PriceService] yfinance batch error: {e}")
            return [PriceQuote(code=c, name=stock_names.get(c), price=None, delayed=True) for c in codes]

        results: list[PriceQuote] = []
        close = df.get("Close")

        for code in codes:
            ticker_tw = f"{code}.TW"
            ticker_two = f"{code}.TWO"
            name = stock_names.get(code)
            try:
                if close is None:
                    raise ValueError("no Close column")

                col = None
                # Single-ticker download returns a Series; multi-ticker returns DataFrame
                if hasattr(close, "columns"):
                    if ticker_tw in close.columns and not close[ticker_tw].dropna().empty:
                        col = close[ticker_tw]
                    elif ticker_two in close.columns and not close[ticker_two].dropna().empty:
                        col = close[ticker_two]
                else:
                    col = close  # Series

                if col is None or col.dropna().empty:
                    raise ValueError("no data")

                col = col.dropna()
                price = float(col.iloc[-1])
                prev = float(col.iloc[-2]) if len(col) >= 2 else None

                results.append(PriceQuote(
                    code=code,
                    name=name,
                    price=price,
                    previous_close=prev,
                    delayed=False,
                    source="yfinance",
                ))
            except Exception as e:
                print(f"[PriceService] parse error for {code}: {e}")
                results.append(PriceQuote(code=code, name=name, price=None, delayed=True))

        return results

    # ------------------------------------------------------------------
    # Benchmark return rate (unchanged)
    # ------------------------------------------------------------------

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
                print(f"[PriceService] benchmark error for {ticker}: {e}")
                return None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fetch)
