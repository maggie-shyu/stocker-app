### May 2, 2026 | Refactor

* [ ] Split the monolithic schema file by domain.[`backend/models/schemas.py`](/Users/meimei/workspace/ntu/repo/stocker/backend/models/schemas.py:1) currently holds transactions, cashflow, holdings, realized, dashboard, and pricing types in one file. It’s still manageable now, but this is a classic file that becomes a dumping ground. A small split like `models/transactions.py`, `models/portfolio.py`, `models/pricing.py` would age better.

- [ ] Consider feature-oriented frontend grouping if the app keeps growing. Today the frontend is still small enough for `pages/`, `api/`, `hooks/`, and `components/`, but you can already see cross-feature concentration in files like [`frontend/src/hooks/queries.ts`](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/hooks/queries.ts:1) and `frontend/src/api/types.ts`. If more screens are coming, a `features/transactions`, `features/holdings`, `features/dashboard` layout will scale better.
