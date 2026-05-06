from __future__ import annotations

from datetime import date, timedelta

import yfinance as yf

from backend.models.domain.portfolio import PriceQuote


class YfinanceQuoteProvider:
    def fetch_quotes(self, codes: list[str], stock_names: dict[str, str]) -> list[PriceQuote]:
        tickers_tw = [f"{code}.TW" for code in codes]
        tickers_two = [f"{code}.TWO" for code in codes]
        tickers = tickers_tw + tickers_two
        try:
            df = yf.download(
                " ".join(tickers),
                period="2d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as exc:
            print(f"[PriceService] yfinance batch error: {exc}")
            return [PriceQuote(code=code, name=stock_names.get(code), price=None, delayed=True) for code in codes]

        results: list[PriceQuote] = []
        close = df.get("Close")

        for code in codes:
            ticker_tw = f"{code}.TW"
            ticker_two = f"{code}.TWO"
            name = stock_names.get(code)
            try:
                if close is None:
                    raise ValueError("no Close column")

                column = None
                if hasattr(close, "columns"):
                    if ticker_tw in close.columns and not close[ticker_tw].dropna().empty:
                        column = close[ticker_tw]
                    elif ticker_two in close.columns and not close[ticker_two].dropna().empty:
                        column = close[ticker_two]
                else:
                    column = close

                if column is None or column.dropna().empty:
                    raise ValueError("no data")

                column = column.dropna()
                price = float(column.iloc[-1])
                previous_close = float(column.iloc[-2]) if len(column) >= 2 else None

                results.append(
                    PriceQuote(
                        code=code,
                        name=name,
                        price=price,
                        previous_close=previous_close,
                        delayed=False,
                        source="yfinance",
                    )
                )
            except Exception as exc:
                print(f"[PriceService] parse error for {code}: {exc}")
                results.append(PriceQuote(code=code, name=name, price=None, delayed=True))

        return results

    def get_benchmark_return_rate(self, ticker: str, start_date: date) -> float | None:
        today = date.today()
        if start_date > today:
            return None

        try:
            df = yf.Ticker(ticker).history(
                start=start_date - timedelta(days=7),
                end=today + timedelta(days=2),
            )
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
        except Exception as exc:
            print(f"[PriceService] benchmark error for {ticker}: {exc}")
            return None
