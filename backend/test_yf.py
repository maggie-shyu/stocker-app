import yfinance as yf

codes = ["00679B", "00751B", "2330"]
tickers_tw = [f"{c}.TW" for c in codes]
tickers_two = [f"{c}.TWO" for c in codes]
tickers = tickers_tw + tickers_two

df = yf.download(" ".join(tickers), period="2d", auto_adjust=True, progress=False, threads=True)
close = df.get("Close")

for code in codes:
    ticker_tw = f"{code}.TW"
    ticker_two = f"{code}.TWO"
    col = None
    if hasattr(close, "columns"):
        if ticker_tw in close.columns and not close[ticker_tw].dropna().empty:
            col = close[ticker_tw]
            print(f"Found {ticker_tw}")
        elif ticker_two in close.columns and not close[ticker_two].dropna().empty:
            col = close[ticker_two]
            print(f"Found {ticker_two}")
    else:
        col = close
    
    if col is not None and not col.dropna().empty:
        col = col.dropna()
        price = float(col.iloc[-1])
        print(f"{code} price: {price}")
    else:
        print(f"{code} not found")

