# Stock Portfolio Web App MVP — Implementation Plan

## Context

Build a minimal but polished web app over the existing `股票管理表.xlsx` file. The Excel file is the single source of truth. The app reads from it to compute KPIs and charts, and writes new transactions/cash flows back to it. No database needed.

---

## Excel File Inventory

| Sheet | Role | Read/Write |

|---|---|---|

| 帳戶概況 | Pre-computed portfolio overview (10 holdings + totals) | Read (rows 2-11, cols A-M) |

| 交易紀錄 | All trades (50 rows; cols A-I manual, J-S auto-computed) | Read + Append + Delete |

| 持股狀況 | Empty — reserved | Ignored |

| 出入金 | Cash deposits/withdrawals (4 rows) | Read + Append |

| 股票代號表 | 2,248 stock code ↔ name mappings | Read-only (cached at startup) |

| 手續費 | Commission discount rate in cell B1 (currently 0.0) | Read + Write |

Key observations:

-`手續費!B1 = 0.0` → discount unset → effective fee = min 20 NTD

-`出入金!D` principal column: only row 2 has a snapshot value; compute as `Σ入金 - Σ出金`

- Transaction types in use: `(買,一般)`, `(買,當沖)`, `(賣,一般)`, `(賣,當沖)`, `(股利,一般)`

---

## Tech Stack

| Layer | Choice |

|---|---|

| Backend | Python FastAPI + openpyxl + uvicorn |

| Frontend | React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui |

| Charts | Recharts |

| Server state | TanStack Query v5 |

| Stock prices | TWSE MIS free API (unofficial, no key required) |

| HTTP client (FE) | axios |

| HTTP client (BE) | httpx (async) |

---

## Project Layout

```

stocker/

├── 股票管理表.xlsx              ← never moved

├── 產品文件.md

├── backend/

│   ├── main.py

│   ├── config.py

│   ├── requirements.txt

│   ├── models/schemas.py

│   ├── routers/

│   │   ├── dashboard.py       GET /api/dashboard

│   │   ├── transactions.py    GET/POST/DELETE /api/transactions

│   │   ├── holdings.py        GET /api/holdings

│   │   ├── realized.py        GET /api/realized

│   │   ├── cashflow.py        GET/POST /api/cashflow

│   │   ├── settings.py        GET/PUT /api/settings

│   │   └── stocks.py          GET /api/stocks/search, /prices, /preview-fee

│   └── services/

│       ├── excel_service.py   openpyxl read/write + threading.Lock

│       ├── calculator.py      FIFO, P&L, fee/tax formulas

│       └── price_service.py   TWSE MIS API + TTLCache

└── frontend/

    └── src/

        ├── api/               one file per resource

        ├── pages/             Dashboard, Transactions, Holdings, Realized, CashFlow, Settings

        ├── components/        layout/, dashboard/, transactions/, holdings/, realized/, cashflow/, shared/

        └── hooks/             useDashboard, useTransactions, useHoldings, …

```

---

## API Endpoints

### GET /api/dashboard

Returns all KPIs + pie data + recent 3 transactions in one call.

```json

{

"account_value":6547207.8,   // stock_market_value + cash_balance

"principal":2670399.0,       // Σ入金 - Σ出金

"stock_market_value":6363700.0,

"cash_balance":183507.8,

"unrealized_pnl":1500000.0,

"unrealized_pnl_rate":0.308,

"realized_pnl":953960.27,

"account_pnl":3876808.8,     // account_value - principal (no withdrawals exist yet)

"account_pnl_rate":1.4518,

"today_pnl":-45000.0,

"dividend_income":7506.0,

"holdings_pie": [{"code":"3163","name":"波若威","market_value":1070000,"weight":0.163}],

"recent_transactions": [...]

}

```

### GET /api/transactions?action=買&code=3163&from_date=2025-08-01&page=1&page_size=50

### POST /api/transactions

```json

{

"date":"2026-05-01", "action":"買", "code":"2330", "name":"台積電",

"trade_type":"一般", "buy_shares":1000, "buy_price":2215.0, "reason":""

}

```

Backend fetches curr_price, computes fees, appends row to 交易紀錄 cols A-S, returns saved record.

### DELETE /api/transactions/

### GET /api/holdings

FIFO-computed from transactions. Per stock: lots, total_shares, avg_cost, market_value, unrealized_pnl, weight.

### GET /api/realized?code=&from_date=&to_date=

Returns realized trades + win_rate, avg_win, avg_loss.

### GET /api/cashflow

### POST /api/cashflow `{date, deposit, withdrawal, is_principal}`

### GET /api/settings

### PUT /api/settings `{commission_discount_rate: 0.6}`

Writes to `手續費!B1`.

### GET /api/stocks/search?q=台積電

Autocomplete from in-memory 股票代號表 cache. Returns top 20.

### GET /api/stocks/prices?codes=2330,3163

TWSE MIS API: `https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw|otc_3163.tw`

TTLCache with 1-second TTL. Tries `tse_` first, falls back to `otc_` if empty `z` field.

### GET /api/stocks/preview-fee?action=買&amount=224500&trade_type=一般

Returns live fee calculation for form preview.

---

## Key Calculations (`services/calculator.py`)

### Fee

```

raw_fee = amount × 0.001425

disc_fee = max(raw_fee × discount_rate, 20)   # discount_rate=0 → fee=20 NTD

tax = amount × 0.003  if 賣/一般

    = amount × 0.0015 if 賣/當沖

    = 0               if 買 or 股利

expense = amount + disc_fee + tax  (for 買)

income  = amount - disc_fee - tax  (for 賣)

```

### FIFO Holdings (deque per stock code)

- 買 → `deque.append({date, shares, cost_per_share = expense/shares})`
- 賣 → drain from front, track consumed cost for realized P&L
- 股利 (cash) → no share change; income recorded

### KPI

```

cash_balance = Σ出入金.deposit - Σ出入金.withdrawal

             - Σtx.expense(買) + Σtx.income(賣) + Σtx.income(股利)

account_value = stock_market_value + cash_balance

account_pnl = account_value - principal

```

### Excel Write Columns (交易紀錄 rows A-S)

A=date, B=action, C=code, D=name, E=trade_type, F=buy_shares, G=buy_price,

H=sell_shares, I=sell_price, J=curr_price, K=raw_fee, L=disc_fee, M=tax,

N=amount, O=trade_cost, P=expense, Q=income, R=reason, S=disc_rate

**File locking:**`threading.Lock()` singleton wraps every write (load → modify → save).

---

## Frontend Pages

| Page | Route | Key Components |

|---|---|---|

| Dashboard | `/` | KpiRow (3 cards), AccountSummaryCard, HoldingsPieChart, RecentTransactions |

| Transactions | `/transactions` | TransactionTable + filter tabs + AddTransactionDrawer (BuyForm/SellForm/DividendForm) |

| Holdings | `/holdings` | HoldingsTable with expandable lots (HoldingLots) |

| Realized P&L | `/realized` | RealizedTable + summary stats + RealizedChart (Recharts bar) |

| Cash Flow | `/cashflow` | CashFlowTable + AddCashFlowDialog |

| Settings | `/settings` | Commission discount slider + rate display |

**Shared components:**`StockSearchInput` (autocomplete), `PriceTag` (green/red), `FeePreview` (live calc).

**AppShell:** Sidebar nav with icons (lucide-react) for all 6 pages.

**Vite proxy:**`/api → http://localhost:8000` (no CORS issues in dev).

---

## Implementation Order

1.`backend/config.py` + `models/schemas.py`

2.`services/excel_service.py` (all reads + all writes)

3.`services/calculator.py` (fees, FIFO, KPIs)

4.`services/price_service.py` (TWSE + TTLCache)

5.`main.py` (FastAPI + CORS + startup preload)

6. Routers: settings → stocks → cashflow → transactions → holdings → realized → dashboard
7. Scaffold frontend with Vite, Tailwind, shadcn/ui init

8.`AppShell` + routing

9. Pages: Settings → CashFlow → Transactions → Holdings → Realized → Dashboard

---

## Dev Setup

```bash

# Backend (conda env mei310 or fresh venv)

cdstocker/backend

pipinstall-rrequirements.txt

uvicornmain:app--reload--port8000


# Frontend

cdstocker/frontend

npminstall

npmrundev# port 5173

```

`requirements.txt`: `fastapi`, `uvicorn[standard]`, `openpyxl`, `httpx`, `pydantic`, `cachetools`, `python-multipart`

`package.json` deps: `react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`, `axios`, `recharts`, `date-fns`, `lucide-react` + shadcn/ui components: `button card dialog drawer input label select table tabs badge separator tooltip skeleton`

---

## Verification

1.`GET /api/settings` → `{commission_discount_rate: 0.0}`

2.`GET /api/transactions` → 50 rows

3.`GET /api/holdings` → 9 stocks (filter out 0-share results) + total market value matches Excel

4.`GET /api/realized` → ~18 realized trades, total ≈ 953,960 NTD

5.`GET /api/dashboard` → `account_value ≈ 6,547,207.8`, `principal = 2,670,399`

6.`GET /api/stocks/prices?codes=2330,3163` → live prices from TWSE

7.`POST /api/transactions` (dummy buy) → row appears in `交易紀錄` when Excel opened

8. Dashboard KPIs, pie chart, and recent transactions all render correctly
9. Fee preview: buy 1000 shares @ 100 NTD → `disc_fee=20 NTD` (discount=0), `expense=100,020`

---

## Confirmed Decisions

1.**Python env:**`conda activate mei310`

2.**Sell lot selection:** FIFO auto-only (no lot picker in MVP)

3.**Price fallback:** Show last known price with a `delayed` badge when TWSE API unavailable
