# Refactor codebase architecture

> [$improve-codebase-architecture](~/workspace/harness/skills/mattpocock/improve-codebase-architecture/SKILL.md) I want to refactor the codebase for better maintainability and software hygeine before starting another big upgrade.

<details><summary>17 previous messages</summary>

> I’m using the `improve-codebase-architecture` skill here. First I’m going to read the project’s domain language and ADRs, then I’ll explore the codebase for seams that feel shallow or leaky so I can come back with a focused shortlist of deepening opportunities.
>
> <details><summary>Explored 1 list, ran 1 command</summary>
>
> - Ran `pwd`
>
> <details><summary>Explored 1 list</summary>
>
> - Listed files
>
> </details>
>
> </details>
>
> I’ve confirmed the workspace and I’m tightening the search for project docs now. Next step is to locate the domain glossary and architecture decisions, then I’ll fan out into the code to see where the real friction clusters.
>
> <details><summary>Explored 2 lists</summary>
>
> - Listed files
> - Listed files in `.`
>
> </details>
>
> There doesn’t seem to be a project `CONTEXT.md` or `docs/adr/` directory in this repo, so I’ll treat the code itself and `README.md` as the current source of domain language. I’m splitting the exploration into backend and frontend so we can surface the hotspots faster without guessing.
>
> <details><summary>Explored 1 file</summary>
>
> - Read `./README.md`
>
> </details>
>
> Subagent action
>
> Action: spawnAgent
> Status: inProgress
> Receiver threads: 0
> Prompt: Explore the backend architecture of this repo for maintainability and software hygiene issues. Use the improve-codebase-architecture vocabulary: module, interface, implementation, depth, seam, adapter, leverage, locality. Focus on shallow modules, leaky seams, duplicated orchestration, weak test surfaces, and places where the deletion test suggests a module is not earning its keep. Read only the backend and shared project files you need. Return a concise list of the top 3 backend deepening opportunities with files, problem, solution, and benefits.
>
> Subagent action
>
> Action: spawnAgent
> Status: inProgress
> Receiver threads: 0
> Prompt: Explore the frontend architecture of this repo for maintainability and software hygiene issues. Use the improve-codebase-architecture vocabulary: module, interface, implementation, depth, seam, adapter, leverage, locality. Focus on shallow modules, duplicated page logic, weak seams around API/query state/auth, and testability problems. Read only the frontend and shared project files you need. Return a concise list of the top 3 frontend deepening opportunities with files, problem, solution, and benefits.
>
> I’ve got the project framing from `README.md`. The codebase is small enough that we can be pretty concrete here, so I’m re-running the split exploration without full-history forking and keeping the prompts tightly scoped to backend and frontend hotspots.
>
> Subagent action
>
> Action: spawnAgent
> Status: completed
> Receiver threads: 2
>
> <details><summary>Explored 8 files</summary>
>
> - Read `./backend/main.py`
> - Read `./backend/services/supabase_service.py`
> - Read `./frontend/src/api/query.ts`
> - Read `./frontend/src/hooks/queries.ts`
> - Read `./backend/routers/dashboard.py`
> - Read `./backend/routers/transactions.py`
> - Read `./frontend/src/pages/Dashboard.tsx`
> - Read `./frontend/src/pages/Transactions.tsx`
>
> </details>
>
> The first pass is already showing a pattern: some modules are carrying real behavior, but several pages and routers are acting as orchestration catch-alls. I’m checking a few more files now to separate “big but healthy” modules from places where depth is actually missing.
>
> <details><summary>Explored 3 files, ran 1 command</summary>
>
> <details><summary>Explored 1 file</summary>
>
> - Read `./frontend/src/contexts/AuthContext.tsx`
>
> </details>
>
> - Ran `wc -l backend/services/*.py backend/routers/*.py frontend/src/pages/*.tsx frontend/src/hooks/*.ts frontend/src/api/*.ts frontend/src/components/shared/*.tsx frontend/src/components/shared/*.ts`
>
> <details><summary>Explored 2 files</summary>
>
> - Read `./backend/services/calculator.py`
> - Read `./backend/routers/deps.py`
>
> </details>
>
> </details>
>
> The broad shape is clearer now: backend complexity is concentrated in `calculator.py` and `supabase_service.py`, while frontend complexity is concentrated in page-level modules rather than in reusable deeper modules. I’m sampling the admin/import-export path next because those often hide the least testable orchestration.
>
> <details><summary>Explored 4 files</summary>
>
> - Read `./frontend/src/pages/Settings.tsx`
> - Read `./backend/services/admin_service.py`
> - Read `./backend/routers/export.py`
> - Read `./frontend/src/api/client.ts`
>
> </details>
>
> I’m cross-checking the architecture against the test surface now. That helps distinguish “this module is large” from “this module has no seam, so every change has to be integration-tested through the whole stack.”
>
> <details><summary>Explored 4 files</summary>
>
> - Read `./backend/tests/test_api.py`
> - Read `./backend/tests/test_supabase_service.py`
> - Read `./frontend/src/pages/Admin.tsx`
> - Read `./frontend/src/App.tsx`
>
> </details>

</details>

I didn’t find a project `CONTEXT.md` or `docs/adr/`, so I used the repo’s existing domain terms from `README.md` and the code itself.

1. **Deepen the portfolio read module**
   Files: [dashboard.py](./backend/routers/dashboard.py), [holdings.py](./backend/routers/holdings.py), [realized.py](./backend/routers/realized.py), [calculator.py](./backend/services/calculator.py)
   Problem: the seam between HTTP and portfolio implementation is leaky. Multiple router modules repeat orchestration around transactions, cashflows, quotes, benchmark dates, and `compute_portfolio`, so callers need to know too much about the implementation.
   Solution: move portfolio assembly behind one deeper module so routes stop rebuilding the same read flow in slightly different ways.
   Benefits: better locality for portfolio rules, more leverage for every route that needs portfolio data, and a stronger test surface because tests can exercise one module instead of several duplicated paths.
2. **Split the Supabase module by domain concept**
   Files: [supabase_service.py](./backend/services/supabase_service.py), [deps.py](./backend/routers/deps.py), [transactions.py](./backend/routers/transactions.py), [cashflow.py](./backend/routers/cashflow.py)
   Problem: `SupabaseService` is a wide module with a broad interface and mixed implementation: CRUD, row mapping, settings defaults, stock lookup, and transaction financial recomputation all live together. The seam is mostly hypothetical because callers depend on the concrete adapter directly.
   Solution: separate persistence concerns into smaller domain-focused modules and keep Supabase as the adapter behind those seams.
   Benefits: higher locality for persistence changes, more leverage from narrower modules, and easier tests because callers can target real seams instead of patching one large concrete module.
3. **Deepen the ledger page module**
   Files: [Transactions.tsx](./frontend/src/pages/Transactions.tsx), [CashFlow.tsx](./frontend/src/pages/CashFlow.tsx), [Realized.tsx](./frontend/src/pages/Realized.tsx), [Admin.tsx](./frontend/src/pages/Admin.tsx)
   Problem: these page modules are shallow. Their interface is just “render a page,” but their implementation also owns pagination, sort state, responsive sizing, input styling side effects, and row-range formatting. The same behavior is repeated across several pages.
   Solution: consolidate shared ledger/table behavior behind a deeper module so pages become thin adapters over domain-specific behavior.
   Benefits: better locality for sorting and pagination behavior, more leverage across all data-heavy pages, and improved testability because shared behavior can be tested once at the seam.
4. **Create a real auth/query seam on the frontend**
   Files: [client.ts](./frontend/src/api/client.ts), [query.ts](./frontend/src/api/query.ts), [queries.ts](./frontend/src/hooks/queries.ts), [AuthContext.tsx](./frontend/src/contexts/AuthContext.tsx)
   Problem: auth state, transport, and query orchestration are tightly coupled. The axios adapter reaches into Supabase directly, and many hooks are thin pass-through modules over path strings, so the seam has low depth.
   Solution: separate session concerns from data-fetch concerns so pages depend on a deeper frontend data module instead of raw transport details.
   Benefits: better locality for auth and error-handling changes, more leverage when the API or auth flow changes, and a cleaner test surface for hooks and route guards.
5. **Separate browser-side orchestration from page implementation**
   Files: [Settings.tsx](./frontend/src/pages/Settings.tsx), [App.tsx](./frontend/src/App.tsx), [App.test.tsx](./frontend/src/App.test.tsx)
   Problem: behavior-heavy pages mix mutation orchestration with browser APIs like `window`, `document`, file download, and modal state. That weakens locality and pushes tests toward app-wide mocking instead of testing through the module interface.
   Solution: move browser-specific behavior behind adapters and let page modules focus on orchestration.
   Benefits: more stable tests, better locality for UI behavior changes, and less brittle app-level wiring.

Which of these would you like to explore?

> All of these. Also, I want to clean up unused files, and identify the appropriate location (folder) for each file to place.

<details><summary>2 previous messages</summary>

> You want a full architecture pass rather than a single candidate, so I’m treating this as a repo-wide deepening exercise plus a hygiene sweep. I’m checking import/reference usage now so I can separate “currently awkward but load-bearing” files from files and folders that can likely be deleted or moved with confidence.
>
> <details><summary>Explored 2 files, 1 search, 1 list</summary>
>
> - Searched for `test_yf|CsvFixtureService|MetricCard|SortableHeader|AdminRouteGuard|RouteGuard|useApiQuery|SupabaseService|PriceService|AdminService` in `backend`
> - Read `./backend/test_yf.py`
> - Read `./backend/tests/support/csv_fixture_service.py`
> - Listed files in `backend`
>
> </details>

</details>

We should treat this as one coordinated refactor, but not as one giant patch. The safest order is:

1. Repository hygiene and folder layout
2. Backend deepening
3. Frontend deepening
4. Test re-seaming

**Repo Shape**
I’d recommend this target layout.

`backend/`

- `main.py`: app entrypoint only
- `api/` or keep `routers/`: HTTP modules only
- `domain/portfolio/`: portfolio read module, holdings, realized logic, trade financials
- `domain/ledger/`: transaction, cashflow, settings interfaces
- `infrastructure/supabase/`: Supabase adapters
- `infrastructure/market_data/`: yfinance adapter and price-fetch implementation
- `admin/` or `domain/admin/`: admin metrics read module if it stays product code
- `tests/unit/`: domain tests
- `tests/integration/`: API and adapter tests
- `tests/support/`: fixtures and fake adapters

`frontend/src/`

- `app/`: routes, providers, shell composition
- `features/portfolio/`: dashboard and holdings read modules
- `features/ledger/`: transactions, cashflow, realized, shared ledger table behavior
- `features/settings/`: settings page and mutations
- `features/admin/`: admin page and admin queries
- `features/auth/`: auth context, guards, session seam
- `platform/api/`: axios adapter
- `platform/auth/`: Supabase auth adapter
- `platform/browser/`: download, DOM, resize helpers
- `shared/ui/`: reusable UI primitives
- `shared/lib/`: generic formatting utilities only

**Deepening Plan**
Here’s how I’d grill each seam.

1. **Portfolio read module**
   Files: [dashboard.py](./backend/routers/dashboard.py), [holdings.py](./backend/routers/holdings.py), [realized.py](./backend/routers/realized.py), [calculator.py](./backend/services/calculator.py)
   Problem: portfolio routes know too much about implementation order.
   Solution: add one deep module behind a seam like `PortfolioReadModule`.
   Interface:

- `load_dashboard(user_id)`
- `load_holdings(user_id)`
- `load_realized(user_id)`
  Implementation behind the seam:
- read ledger data
- resolve quotes
- compute portfolio
- shape route-specific output
  Tests that survive:
- unit tests for portfolio assembly
- thin route tests for status codes and response wiring

2. **Ledger and stock catalog seams**
   Files: [supabase_service.py](./backend/services/supabase_service.py), [deps.py](./backend/routers/deps.py)
   Problem: one wide concrete module mixes several concepts.
   Solution: split into:

- `LedgerStore` for transactions, cashflows, settings
- `StockCatalog` for stock search/lookups
- `AdminStore` if admin table browsing remains
  Adapters:
- `SupabaseLedgerStore`
- `SupabaseStockCatalog`
  Benefits:
- better locality
- smaller interfaces
- easier fake adapters in tests

3. **Market data seam**
   Files: [price_service.py](./backend/services/price_service.py), [stocks.py](./backend/routers/stocks.py)
   Problem: `PriceService` mixes orchestration with provider details.
   Solution:

- keep a deep `PriceService`
- move upstream details behind `QuoteProvider`
  Adapter:
- `YFinanceQuoteProvider`
  Tests that survive:
- `PriceService` tested against fake provider
- adapter tested separately

4. **Ledger page module**
   Files: [Transactions.tsx](./frontend/src/pages/Transactions.tsx), [CashFlow.tsx](./frontend/src/pages/CashFlow.tsx), [Realized.tsx](./frontend/src/pages/Realized.tsx), [Admin.tsx](./frontend/src/pages/Admin.tsx)
   Problem: page modules are shallow and repeat pager/sort/browser behavior.
   Solution: create a deep frontend ledger module.
   Suggested placement:

- `src/features/ledger/hooks/useLedgerTable.ts`
- `src/features/ledger/components/LedgerTable.tsx`
- `src/features/ledger/lib/pagination.ts`
- page files become thin adapters

5. **Frontend auth/query seam**
   Files: [client.ts](./frontend/src/api/client.ts), [query.ts](./frontend/src/api/query.ts), [queries.ts](./frontend/src/hooks/queries.ts), [AuthContext.tsx](./frontend/src/contexts/AuthContext.tsx)
   Problem: transport, session, and query concerns are coupled.
   Solution:

- `platform/api/client.ts`
- `platform/auth/supabaseSession.ts`
- feature-level query modules like `features/portfolio/api.ts`
  This gives pages a real seam instead of raw paths.

6. **Browser adapter seam**
   Files: [Settings.tsx](./frontend/src/pages/Settings.tsx), [App.tsx](./frontend/src/App.tsx)
   Problem: DOM effects and browser APIs are mixed into feature orchestration.
   Solution:

- `platform/browser/downloadFile.ts`
- `platform/browser/useResponsivePageSize.ts`
- `platform/browser/installNumberInputStyles.ts`

**Cleanup Sweep**
High-confidence cleanup candidates:

- `backend/test_yf.py`
  Reason: looks like a manual spike, not imported anywhere.
  Best home if kept: `backend/scripts/test_yf.py`
  Best outcome if not needed: delete it.
- `frontend/dist/`
  Reason: generated build output, should not live in the repo.
  Best home: not in git, regenerate on build.
- `frontend/node_modules/`
  Reason: dependency install output, should not live in the repo.
  Best home: local install only, not in git.
- `backend/__pycache__/`, `backend/tests/__pycache__/`, `frontend/.../__pycache__`
  Reason: generated Python bytecode.
  Best home: local cache only.
- `backend/.pytest_cache/`
  Reason: generated test cache.
  Best home: local cache only.
- `supabase/.temp/`
  Reason: local Supabase CLI state.
  Best home: local temp only.
- `backend/.DS_Store`
  Reason: macOS artifact.
  Best home: nowhere.
- `backend/.env`, `frontend/.env`
  Reason: local secrets/config.
  Best home: local only, not committed.

One extra hygiene signal: there are stale cache entries mentioning old modules like `csv_service` and `excel_service`, but no source files for them now. That strengthens the case for a full generated-file cleanup before refactoring.

**Where Current Files Belong**
A few concrete relocations I’d make:

- [backend/services/calculator.py](./backend/services/calculator.py) -> `backend/domain/portfolio/calculator.py`
- [backend/services/price_service.py](./backend/services/price_service.py) -> `backend/domain/portfolio/price_service.py` or `backend/infrastructure/market_data/price_service.py` depending on whether we keep it orchestration-first
- [backend/services/supabase_service.py](./backend/services/supabase_service.py) -> split across `backend/infrastructure/supabase/`
- [backend/services/admin_service.py](./backend/services/admin_service.py) -> `backend/admin/metrics.py` or `backend/infrastructure/supabase/admin_metrics.py`
- [backend/models/schemas.py](./backend/models/schemas.py) -> split into route contracts vs domain types once the seams are real
- [frontend/src/hooks/queries.ts](./frontend/src/hooks/queries.ts) -> split into feature folders
- [frontend/src/api/query.ts](./frontend/src/api/query.ts) -> `frontend/src/platform/api/query.ts`
- [frontend/src/api/client.ts](./frontend/src/api/client.ts) -> `frontend/src/platform/api/client.ts`
- [frontend/src/contexts/AuthContext.tsx](./frontend/src/contexts/AuthContext.tsx) -> `frontend/src/features/auth/AuthContext.tsx`
- [frontend/src/components/RouteGuard.tsx](./frontend/src/components/RouteGuard.tsx) -> `frontend/src/features/auth/RouteGuard.tsx`
- [frontend/src/components/AdminRouteGuard.tsx](./frontend/src/components/AdminRouteGuard.tsx) -> `frontend/src/features/auth/AdminRouteGuard.tsx`
- [frontend/src/components/shared/sort.ts](./frontend/src/components/shared/sort.ts) -> `frontend/src/features/ledger/lib/sort.ts`
- [frontend/src/components/shared/format.ts](./frontend/src/components/shared/format.ts) -> `frontend/src/shared/lib/format.ts`

**Recommendation**
I’d start with a non-behavioral hygiene pass plus folder reshaping, then refactor backend seams, then frontend seams. That gives us maximum locality and the lowest regression risk before the “big upgrade.”

1. I can turn this into a concrete file-by-file move plan and cleanup checklist.
2. I can start implementing Phase 1 now: remove generated junk, move the obvious misfit files, and create the target folder structure.
3. I can start with backend deepening first if you want the highest leverage seam before any frontend moves.

> Turn this into a concrete file-by-file move plan and cleanup checklist. Save it to .docs folder.

<details><summary>6 previous messages</summary>

> I’m turning the architecture review into an actionable repo document now. First I’m checking whether `.docs/` already exists and what conventions it uses so the plan lands in the right place and format.
>
> <details><summary>Explored 1 search, 1 list</summary>
>
> - Searched for `.docs` in `.`
> - Listed files
>
> </details>
>
> `.docs/` is already present, so I’m going to match that home rather than inventing a new convention. I’m reading the existing doc names and structure briefly, then I’ll write the move plan and cleanup checklist into a dedicated architecture file.
>
> <details><summary>Explored 1 file, 1 list</summary>
>
> - Listed files in `.docs`
> - Read `./.docs/TODO.md`
>
> </details>
>
> I have enough context to write this cleanly. I’m creating a dedicated `.docs` plan that turns the review into a phase-by-phase checklist, with explicit source-to-target moves and a cleanup pass split into high-confidence deletes versus “decide before removing.”
>
> <details><summary>Created 1 file</summary>
>
> - Wrote `./.docs/architecture-refactor-move-plan.md` (+422 -0)
>
> </details>

</details>

Saved the concrete move plan and cleanup checklist to [.docs/architecture-refactor-move-plan.md](./.docs/architecture-refactor-move-plan.md).

It includes:

- target backend and frontend folder layouts
- phased cleanup and refactor order
- file-by-file move table
- high-confidence delete/ignore checklist
- decision points for ambiguous files like [backend/test_yf.py](./backend/test_yf.py)

No code behavior changed, so I didn’t run tests.

1. I can turn this into an execution checklist with PR-sized batches next.
2. I can start Phase 0 and Phase 1 directly from the new doc.
