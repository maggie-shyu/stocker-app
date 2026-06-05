from __future__ import annotations

from datetime import date, timedelta

import yfinance as yf

from backend.models.domain.portfolio import PriceQuote


class YfinanceQuoteProvider:
    def fetch_quotes(self, codes: list[str], stock_names: dict[str, str]) -> list[PriceQuote]:
        # Step 1: try all as .TW first (TWSE); collect those with no data for .TWO fallback
        tw_close = self._download_close([f"{c}.TW" for c in codes], ".TW batch")
        missing = [c for c in codes if not self._has_data(tw_close, f"{c}.TW")]

        # Step 2: fetch only the codes that had no .TW data
        two_close = self._download_close([f"{c}.TWO" for c in missing], ".TWO fallback") if missing else None

        results: list[PriceQuote] = []
        for code in codes:
            name = stock_names.get(code)
            col = self._pick_column(tw_close, f"{code}.TW")
            if col is None:
                col = self._pick_column(two_close, f"{code}.TWO")
            if col is None:
                results.append(PriceQuote(code=code, name=name, price=None, delayed=True))
                continue
            try:
                col = col.dropna()
                results.append(PriceQuote(
                    code=code,
                    name=name,
                    price=float(col.iloc[-1]),
                    previous_close=float(col.iloc[-2]) if len(col) >= 2 else None,
                    delayed=False,
                    source="yfinance",
                ))
            except Exception as exc:
                print(f"[PriceService] parse error for {code}: {exc}")
                results.append(PriceQuote(code=code, name=name, price=None, delayed=True))

        return results

    def _download_close(self, tickers: list[str], label: str):
        """Download 2d Close data for tickers; returns Close df or None on error."""
        if not tickers:
            return None
        try:
            df = yf.download(" ".join(tickers), period="2d", auto_adjust=True, progress=False, threads=True)
            return df.get("Close")
        except Exception as exc:
            print(f"[PriceService] yfinance error ({label}): {exc}")
            return None

    def _has_data(self, close, ticker: str) -> bool:
        if close is None:
            return False
        if hasattr(close, "columns"):
            return ticker in close.columns and not close[ticker].dropna().empty
        return not close.dropna().empty  # single-ticker df has no columns level

    def _pick_column(self, close, ticker: str):
        """Return the Series for ticker, or None if unavailable."""
        if close is None:
            return None
        if hasattr(close, "columns"):
            if ticker in close.columns and not close[ticker].dropna().empty:
                return close[ticker]
            return None
        # single-ticker download returns a plain Series
        return close if not close.dropna().empty else None

    def get_benchmark_return_rate(self, ticker: str, start_date: date) -> float | None:
        today = date.today()
        if start_date > today:
            return None

        try:
            # auto_adjust=True → Close = dividend-adjusted price (還原股價)
            df = yf.Ticker(ticker).history(
                start=start_date - timedelta(days=7),
                end=today + timedelta(days=2),
                auto_adjust=True,
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
