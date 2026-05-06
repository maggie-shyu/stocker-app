# Architecture Refactor Move Plan

Last updated: 2026-05-05

## Goal

Prepare the repo for a larger upgrade by:

- deepening shallow modules
- improving locality around portfolio, ledger, auth, and browser behavior
- removing generated or stray files
- moving files into folders that better match their role

This plan is intentionally split into low-risk phases so we can improve software hygiene before changing behavior.

## Guiding Terms

- **Module**: a file or group of files with an interface and an implementation
- **Seam**: where an interface lives and where adapters can be swapped
- **Adapter**: the concrete integration with Supabase, yfinance, axios, Supabase auth, or browser APIs
- **Locality**: change stays in one place
- **Leverage**: callers get more behavior from a smaller interface

## Recommended Target Layout

### Backend

```text
backend/
  main.py
  config.py
  api/
    admin.py
    cashflow.py
    dashboard.py
    deps.py
    export.py
    holdings.py
    realized.py
    settings.py
    stocks.py
    transactions.py
  domain/
    portfolio/
      calculator.py
      read_module.py
      price_service.py
    ledger/
      interfaces.py
    admin/
      metrics.py
  infrastructure/
    supabase/
      ledger_store.py
      stock_catalog.py
      admin_store.py
    market_data/
      yfinance_quote_provider.py
  models/
    api/
    domain/
  tests/
    unit/
    integration/
    support/
```

### Frontend

```text
frontend/src/
  app/
    App.tsx
    main.tsx
    routes.tsx
  features/
    admin/
    auth/
    dashboard/
    holdings/
    ledger/
    settings/
  platform/
    api/
    auth/
    browser/
  shared/
    lib/
    ui/
```

## Phase 0: Cleanup Before Refactor

These items should be cleaned before or alongside folder moves so the refactor does not preserve noise.

### High-confidence delete or ignore

- [ ] Remove [backend/.DS_Store](/Users/meimei/workspace/ntu/repo/stocker/backend/.DS_Store)
- [ ] Remove [./.docs/.DS_Store](/Users/meimei/workspace/ntu/repo/stocker/.docs/.DS_Store)
- [ ] Remove all `__pycache__/` folders under `backend/`
- [ ] Remove [backend/.pytest_cache/](/Users/meimei/workspace/ntu/repo/stocker/backend/.pytest_cache) if present
- [ ] Remove root [/.pytest_cache/](/Users/meimei/workspace/ntu/repo/stocker/.pytest_cache) from version control if tracked
- [ ] Remove [frontend/dist/](/Users/meimei/workspace/ntu/repo/stocker/frontend/dist) from version control if tracked
- [ ] Remove [frontend/node_modules/](/Users/meimei/workspace/ntu/repo/stocker/frontend/node_modules) from version control if tracked
- [ ] Remove [supabase/.temp/](/Users/meimei/workspace/ntu/repo/stocker/supabase/.temp) from version control if tracked
- [ ] Ensure [backend/.env](/Users/meimei/workspace/ntu/repo/stocker/backend/.env) and [frontend/.env](/Users/meimei/workspace/ntu/repo/stocker/frontend/.env) stay untracked
- [ ] Ensure [/.coverage](/Users/meimei/workspace/ntu/repo/stocker/.coverage) stays untracked

### Decide before removing

- [ ] Review [backend/test_yf.py](/Users/meimei/workspace/ntu/repo/stocker/backend/test_yf.py)
  Reason: looks like a one-off manual market data spike, not product code or test code.
  Recommendation:
  - delete if no longer needed
  - otherwise move to `backend/scripts/test_yf.py`

### Gitignore follow-up

- [ ] Confirm `.gitignore` covers:
  - `.DS_Store`
  - `__pycache__/`
  - `.pytest_cache/`
  - `.coverage`
  - `frontend/dist/`
  - `frontend/node_modules/`
  - `supabase/.temp/`
  - `backend/.env`
  - `frontend/.env`

## Phase 1: Low-risk Folder Renames

This phase should be mostly move-only, with import updates but minimal behavior change.

### Backend API folder

If we want the folder name to reflect role more clearly, rename `routers` to `api`.

- [ ] Move [backend/routers/admin.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/admin.py) -> `backend/api/admin.py`
- [ ] Move [backend/routers/cashflow.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/cashflow.py) -> `backend/api/cashflow.py`
- [ ] Move [backend/routers/dashboard.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/dashboard.py) -> `backend/api/dashboard.py`
- [ ] Move [backend/routers/deps.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/deps.py) -> `backend/api/deps.py`
- [ ] Move [backend/routers/export.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/export.py) -> `backend/api/export.py`
- [ ] Move [backend/routers/holdings.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/holdings.py) -> `backend/api/holdings.py`
- [ ] Move [backend/routers/realized.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/realized.py) -> `backend/api/realized.py`
- [ ] Move [backend/routers/settings.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/settings.py) -> `backend/api/settings.py`
- [ ] Move [backend/routers/stocks.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/stocks.py) -> `backend/api/stocks.py`
- [ ] Move [backend/routers/transactions.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/transactions.py) -> `backend/api/transactions.py`
- [ ] Move [backend/routers/__init__.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/__init__.py) -> `backend/api/__init__.py`

### Frontend shared path clarifications

These moves improve naming without committing yet to deeper feature refactors.

- [ ] Move [frontend/src/api/client.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/api/client.ts) -> `frontend/src/platform/api/client.ts`
- [ ] Move [frontend/src/api/query.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/api/query.ts) -> `frontend/src/platform/api/query.ts`
- [ ] Move [frontend/src/lib/supabase.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/lib/supabase.ts) -> `frontend/src/platform/auth/supabase.ts`
- [ ] Move [frontend/src/components/RouteGuard.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/RouteGuard.tsx) -> `frontend/src/features/auth/RouteGuard.tsx`
- [ ] Move [frontend/src/components/AdminRouteGuard.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/AdminRouteGuard.tsx) -> `frontend/src/features/auth/AdminRouteGuard.tsx`
- [ ] Move [frontend/src/contexts/AuthContext.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/contexts/AuthContext.tsx) -> `frontend/src/features/auth/AuthContext.tsx`
- [ ] Move [frontend/src/components/shared/UI.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/shared/UI.tsx) -> `frontend/src/shared/ui/UI.tsx`
- [ ] Move [frontend/src/components/shared/MetricCard.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/shared/MetricCard.tsx) -> `frontend/src/shared/ui/MetricCard.tsx`
- [ ] Move [frontend/src/components/shared/format.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/shared/format.ts) -> `frontend/src/shared/lib/format.ts`
- [ ] Move [frontend/src/components/shared/format.test.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/shared/format.test.ts) -> `frontend/src/shared/lib/format.test.ts`

## Phase 2: Backend Deepening

This phase creates real seams and moves files into concept-based folders.

### 2A. Portfolio read module

Goal: routes stop orchestrating portfolio assembly directly.

- [ ] Create `backend/domain/portfolio/read_module.py`
- [ ] Move or extract portfolio assembly logic from [backend/routers/dashboard.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/dashboard.py)
- [ ] Move or extract portfolio assembly logic from [backend/routers/holdings.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/holdings.py)
- [ ] Move or extract portfolio assembly logic from [backend/routers/realized.py](/Users/meimei/workspace/ntu/repo/stocker/backend/routers/realized.py)
- [ ] Move [backend/services/calculator.py](/Users/meimei/workspace/ntu/repo/stocker/backend/services/calculator.py) -> `backend/domain/portfolio/calculator.py`

Suggested result:

- `read_module.py` owns:
  - reading ledger data
  - collecting stock codes
  - fetching quotes
  - building `PriceStatus`
  - computing benchmark return windows
  - shaping dashboard, holdings, and realized outputs

### 2B. Split the Supabase module by domain concept

Goal: replace one wide concrete module with narrower interfaces and adapters.

Current source:

- [backend/services/supabase_service.py](/Users/meimei/workspace/ntu/repo/stocker/backend/services/supabase_service.py)

Planned split:

- [ ] Create `backend/domain/ledger/interfaces.py`
- [ ] Create `backend/infrastructure/supabase/ledger_store.py`
- [ ] Create `backend/infrastructure/supabase/stock_catalog.py`
- [ ] Create `backend/infrastructure/supabase/admin_store.py`

Move responsibilities:

- [ ] Move transaction CRUD from [backend/services/supabase_service.py](/Users/meimei/workspace/ntu/repo/stocker/backend/services/supabase_service.py) -> `backend/infrastructure/supabase/ledger_store.py`
- [ ] Move cashflow CRUD from [backend/services/supabase_service.py](/Users/meimei/workspace/ntu/repo/stocker/backend/services/supabase_service.py) -> `backend/infrastructure/supabase/ledger_store.py`
- [ ] Move settings read/write from [backend/services/supabase_service.py](/Users/meimei/workspace/ntu/repo/stocker/backend/services/supabase_service.py) -> `backend/infrastructure/supabase/ledger_store.py`
- [ ] Move stock search and stock read logic from [backend/services/supabase_service.py](/Users/meimei/workspace/ntu/repo/stocker/backend/services/supabase_service.py) -> `backend/infrastructure/supabase/stock_catalog.py`

### 2C. Market data adapter seam

Goal: keep a deep price module while hiding provider-specific behavior behind an adapter.

- [ ] Move [backend/services/price_service.py](/Users/meimei/workspace/ntu/repo/stocker/backend/services/price_service.py) -> `backend/domain/portfolio/price_service.py`
- [ ] Create `backend/infrastructure/market_data/yfinance_quote_provider.py`
- [ ] Extract yfinance-specific fetching and parsing into that adapter
- [ ] Keep orchestration, cache policy, and portfolio-facing interface inside `price_service.py`

### 2D. Admin metrics module

Goal: separate admin metrics concerns from generic services.

- [ ] Move [backend/services/admin_service.py](/Users/meimei/workspace/ntu/repo/stocker/backend/services/admin_service.py) -> `backend/admin/metrics.py`

Later, if useful:

- [ ] Extract metrics fetching into `backend/infrastructure/supabase/admin_metrics.py`
- [ ] Keep table-browsing orchestration in `backend/admin/metrics.py`

### 2E. Models cleanup

Current source:

- [backend/models/schemas.py](/Users/meimei/workspace/ntu/repo/stocker/backend/models/schemas.py)

Planned split:

- [ ] Create `backend/models/api/`
- [ ] Create `backend/models/domain/`
- [ ] Split transaction and cashflow contracts into `backend/models/api/ledger.py`
- [ ] Split dashboard, holdings, realized contracts into `backend/models/api/portfolio.py`
- [ ] Split domain-only structures into `backend/models/domain/`

## Phase 3: Frontend Deepening

### 3A. App composition folder

- [ ] Move [frontend/src/App.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/App.tsx) -> `frontend/src/app/App.tsx`
- [ ] Move [frontend/src/main.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/main.tsx) -> `frontend/src/app/main.tsx`
- [ ] Create `frontend/src/app/routes.tsx`

### 3B. Feature modules

Move page modules into feature folders.

- [ ] Move [frontend/src/pages/Dashboard.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Dashboard.tsx) -> `frontend/src/features/dashboard/DashboardPage.tsx`
- [ ] Move [frontend/src/pages/Holdings.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Holdings.tsx) -> `frontend/src/features/holdings/HoldingsPage.tsx`
- [ ] Move [frontend/src/pages/Transactions.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Transactions.tsx) -> `frontend/src/features/ledger/TransactionsPage.tsx`
- [ ] Move [frontend/src/pages/CashFlow.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/CashFlow.tsx) -> `frontend/src/features/ledger/CashFlowPage.tsx`
- [ ] Move [frontend/src/pages/Realized.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Realized.tsx) -> `frontend/src/features/ledger/RealizedPage.tsx`
- [ ] Move [frontend/src/pages/Settings.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Settings.tsx) -> `frontend/src/features/settings/SettingsPage.tsx`
- [ ] Move [frontend/src/pages/Admin.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Admin.tsx) -> `frontend/src/features/admin/AdminPage.tsx`
- [ ] Move [frontend/src/pages/Login.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Login.tsx) -> `frontend/src/features/auth/LoginPage.tsx`
- [ ] Move [frontend/src/pages/Login.test.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Login.test.tsx) -> `frontend/src/features/auth/LoginPage.test.tsx`

### 3C. Ledger table seam

Goal: shared sort, pager, and browser behavior should live behind one seam.

Current files:

- [frontend/src/pages/Transactions.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Transactions.tsx)
- [frontend/src/pages/CashFlow.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/CashFlow.tsx)
- [frontend/src/pages/Realized.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Realized.tsx)
- [frontend/src/pages/Admin.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Admin.tsx)
- [frontend/src/components/shared/SortableHeader.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/shared/SortableHeader.tsx)
- [frontend/src/components/shared/sort.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/shared/sort.ts)

Planned modules:

- [ ] Create `frontend/src/features/ledger/components/SortableHeader.tsx`
- [ ] Create `frontend/src/features/ledger/lib/sort.ts`
- [ ] Create `frontend/src/features/ledger/hooks/useLedgerTable.ts`
- [ ] Create `frontend/src/platform/browser/useResponsivePageSize.ts`
- [ ] Create `frontend/src/platform/browser/installNumberInputStyles.ts`

Move files:

- [ ] Move [frontend/src/components/shared/SortableHeader.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/shared/SortableHeader.tsx) -> `frontend/src/features/ledger/components/SortableHeader.tsx`
- [ ] Move [frontend/src/components/shared/sort.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/shared/sort.ts) -> `frontend/src/features/ledger/lib/sort.ts`

### 3D. Query modules by feature

Current source:

- [frontend/src/hooks/queries.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/hooks/queries.ts)
- [frontend/src/api/types.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/api/types.ts)

Planned split:

- [ ] Create `frontend/src/features/dashboard/queries.ts`
- [ ] Create `frontend/src/features/ledger/queries.ts`
- [ ] Create `frontend/src/features/settings/queries.ts`
- [ ] Create `frontend/src/features/admin/queries.ts`
- [ ] Split [frontend/src/api/types.ts](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/api/types.ts) by feature when seams stabilize

### 3E. Auth seam

Goal: stop mixing Supabase auth, guards, and app-wide usage in generic folders.

- [ ] Move [frontend/src/contexts/AuthContext.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/contexts/AuthContext.tsx) -> `frontend/src/features/auth/AuthContext.tsx`
- [ ] Move [frontend/src/components/RouteGuard.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/RouteGuard.tsx) -> `frontend/src/features/auth/RouteGuard.tsx`
- [ ] Move [frontend/src/components/AdminRouteGuard.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/components/AdminRouteGuard.tsx) -> `frontend/src/features/auth/AdminRouteGuard.tsx`
- [ ] Create `frontend/src/platform/auth/session.ts`

### 3F. Browser adapters for Settings page

Goal: page orchestration stops owning browser-only details.

- [ ] Create `frontend/src/platform/browser/downloadFile.ts`
- [ ] Move export download logic out of [frontend/src/pages/Settings.tsx](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Settings.tsx) into `downloadFile.ts`
- [ ] Move responsive page-size logic from page files into `useResponsivePageSize.ts`
- [ ] Move runtime input CSS injection into `installNumberInputStyles.ts`

## Phase 4: Test Reshaping

### Backend tests

- [ ] Keep API tests in `backend/tests/integration/`
- [ ] Move portfolio logic tests into `backend/tests/unit/portfolio/`
- [ ] Move price module tests into `backend/tests/unit/portfolio/`
- [ ] Move Supabase adapter tests into `backend/tests/integration/supabase/`
- [ ] Keep [backend/tests/support/csv_fixture_service.py](/Users/meimei/workspace/ntu/repo/stocker/backend/tests/support/csv_fixture_service.py) in `tests/support/` unless we replace it with narrower fakes

Potential later split:

- [ ] If `CsvFixtureService` remains useful, rename it to reflect role more clearly, such as `FixtureLedgerStore`

### Frontend tests

- [ ] Keep app shell wiring tests near `frontend/src/app/`
- [ ] Move auth tests near `frontend/src/features/auth/`
- [ ] Add focused tests for `useLedgerTable`
- [ ] Add focused tests for `downloadFile.ts` and browser adapters only if they carry non-trivial behavior

## File-by-file Move Table

Use this section as the execution checklist during the actual refactor.

### Backend

| Current file | Planned location | Notes |
| --- | --- | --- |
| `backend/routers/admin.py` | `backend/api/admin.py` | move-only in Phase 1 |
| `backend/routers/cashflow.py` | `backend/api/cashflow.py` | move-only in Phase 1 |
| `backend/routers/dashboard.py` | `backend/api/dashboard.py` | later delegate to portfolio read module |
| `backend/routers/deps.py` | `backend/api/deps.py` | update dependency wiring after adapter split |
| `backend/routers/export.py` | `backend/api/export.py` | may later delegate workbook parsing module |
| `backend/routers/holdings.py` | `backend/api/holdings.py` | later delegate to portfolio read module |
| `backend/routers/realized.py` | `backend/api/realized.py` | later delegate to portfolio read module |
| `backend/routers/settings.py` | `backend/api/settings.py` | later delegate to ledger store seam |
| `backend/routers/stocks.py` | `backend/api/stocks.py` | later delegate to stock catalog and price modules |
| `backend/routers/transactions.py` | `backend/api/transactions.py` | later delegate to ledger store seam |
| `backend/services/calculator.py` | `backend/domain/portfolio/calculator.py` | real domain logic |
| `backend/services/price_service.py` | `backend/domain/portfolio/price_service.py` | orchestration stays here |
| `backend/services/supabase_service.py` | split | becomes Supabase adapters, not one file |
| `backend/services/admin_service.py` | `backend/admin/metrics.py` | may later split again |
| `backend/models/schemas.py` | split | divide api vs domain models |
| `backend/test_yf.py` | `backend/scripts/test_yf.py` or delete | manual spike |

### Frontend

| Current file | Planned location | Notes |
| --- | --- | --- |
| `frontend/src/App.tsx` | `frontend/src/app/App.tsx` | app composition |
| `frontend/src/main.tsx` | `frontend/src/app/main.tsx` | app bootstrap |
| `frontend/src/api/client.ts` | `frontend/src/platform/api/client.ts` | transport adapter |
| `frontend/src/api/query.ts` | `frontend/src/platform/api/query.ts` | query helper adapter |
| `frontend/src/api/types.ts` | split by feature later | avoid early churn |
| `frontend/src/lib/supabase.ts` | `frontend/src/platform/auth/supabase.ts` | auth adapter |
| `frontend/src/contexts/AuthContext.tsx` | `frontend/src/features/auth/AuthContext.tsx` | feature-owned auth seam |
| `frontend/src/components/RouteGuard.tsx` | `frontend/src/features/auth/RouteGuard.tsx` | auth seam |
| `frontend/src/components/AdminRouteGuard.tsx` | `frontend/src/features/auth/AdminRouteGuard.tsx` | auth seam |
| `frontend/src/hooks/queries.ts` | split into feature query files | avoid central query dumping ground |
| `frontend/src/pages/Admin.tsx` | `frontend/src/features/admin/AdminPage.tsx` | admin feature |
| `frontend/src/pages/CashFlow.tsx` | `frontend/src/features/ledger/CashFlowPage.tsx` | ledger feature |
| `frontend/src/pages/Dashboard.tsx` | `frontend/src/features/dashboard/DashboardPage.tsx` | dashboard feature |
| `frontend/src/pages/Holdings.tsx` | `frontend/src/features/holdings/HoldingsPage.tsx` | holdings feature |
| `frontend/src/pages/Login.tsx` | `frontend/src/features/auth/LoginPage.tsx` | auth feature |
| `frontend/src/pages/Login.test.tsx` | `frontend/src/features/auth/LoginPage.test.tsx` | auth test |
| `frontend/src/pages/Realized.tsx` | `frontend/src/features/ledger/RealizedPage.tsx` | ledger feature |
| `frontend/src/pages/Settings.tsx` | `frontend/src/features/settings/SettingsPage.tsx` | settings feature |
| `frontend/src/pages/Transactions.tsx` | `frontend/src/features/ledger/TransactionsPage.tsx` | ledger feature |
| `frontend/src/components/shared/UI.tsx` | `frontend/src/shared/ui/UI.tsx` | shared UI primitives |
| `frontend/src/components/shared/MetricCard.tsx` | `frontend/src/shared/ui/MetricCard.tsx` | shared UI primitive |
| `frontend/src/components/shared/SortableHeader.tsx` | `frontend/src/features/ledger/components/SortableHeader.tsx` | ledger-specific UI |
| `frontend/src/components/shared/sort.ts` | `frontend/src/features/ledger/lib/sort.ts` | ledger-specific logic |
| `frontend/src/components/shared/format.ts` | `frontend/src/shared/lib/format.ts` | generic formatting |
| `frontend/src/components/shared/format.test.ts` | `frontend/src/shared/lib/format.test.ts` | generic formatting test |

## Suggested Execution Order

- [ ] Phase 0 cleanup
- [ ] Phase 1 move-only folder cleanup
- [ ] Phase 2 backend deepening
- [ ] Phase 3 frontend deepening
- [ ] Phase 4 test reshaping

## Out of Scope for the First Pass

- redesigning API payloads unless needed by seams
- changing core business rules in portfolio calculations
- replacing Supabase or yfinance
- redesigning the UI

## Ready-for-Implementation Checklist

- [ ] Confirm whether `routers/` should be renamed to `api/` now or later
- [ ] Confirm whether `backend/test_yf.py` should be deleted or kept as a script
- [ ] Decide whether `backend/models/schemas.py` should be split early or after adapter extraction
- [ ] Decide whether feature-folder moves on the frontend should happen before or after `useLedgerTable` extraction
