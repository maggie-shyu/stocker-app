# Backend Multi-User Design

**Date:** 2026-05-01
**Status:** Approved

## Overview

Migrate stocker from a single-user CSV/JSON backend to a multi-user system using Supabase (Postgres + Auth). Add Excel export to the settings page.

---

## Architecture

```
React Frontend (Vite)
  │  1. sign in → Supabase Auth (email/password)
  │  2. receives JWT access token
  │  3. sends JWT as Bearer token on every API call
  ▼
FastAPI Backend
  │  4. verifies JWT using SUPABASE_JWT_SECRET → extracts user_id
  │  5. scopes all Supabase DB queries to user_id
  ▼
Supabase
  ├─ Auth  — manages users, sessions, future OAuth (Google, etc.)
  └─ Postgres — transactions, cashflow, stocks, user_settings (per-user rows)
```

The frontend uses the Supabase JS client only for auth. All business logic (holdings calculations, dashboard, realized gains, etc.) remains unchanged in FastAPI. The `csv_service.py` is replaced by `supabase_service.py` with the same interface.

---

## Authentication

**Phase 1 (MVP):** Email/password only via Supabase Auth.  
**Phase 2 (future):** Google OAuth — enable in Supabase dashboard, zero backend changes required.

### Frontend flow
```typescript
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// sign up
await supabase.auth.signUp({ email, password })

// sign in — returns JWT access token
const { data } = await supabase.auth.signInWithPassword({ email, password })
// attach data.session.access_token as Bearer token to all FastAPI requests
```

### Backend verification
```python
# routers/deps.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
    return payload["sub"]  # user_id (uuid)
```

`SUPABASE_JWT_SECRET` is loaded from `.env`, never hardcoded. All routers gain `user_id: str = Depends(get_current_user)` and pass it to the service layer.

---

## Database Schema

All tables use RLS (Row-Level Security) with policy `user_id = auth.uid()` so Supabase enforces data isolation even if FastAPI has a bug.

```sql
-- transactions
CREATE TABLE transactions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid REFERENCES auth.users NOT NULL,
    date            date NOT NULL,
    action          text NOT NULL,       -- 買 / 賣 / 股利
    code            text NOT NULL,
    name            text NOT NULL,
    trade_type      text NOT NULL DEFAULT '一般',
    buy_shares      numeric,
    buy_price       numeric,
    sell_shares     numeric,
    sell_price      numeric,
    dividend_income numeric,
    reason          text
);

-- cashflow
CREATE TABLE cashflow (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid REFERENCES auth.users NOT NULL,
    date                date NOT NULL,
    deposit             numeric NOT NULL DEFAULT 0,
    withdrawal          numeric NOT NULL DEFAULT 0,
    principal_snapshot  numeric
);

-- stocks (global reference table — Taiwan stock code/name lookup for autocomplete)
-- no user_id: shared across all users, populated once from stocks.csv
CREATE TABLE stocks (
    code    text PRIMARY KEY,
    name    text NOT NULL
);

-- user_settings
CREATE TABLE user_settings (
    user_id                 uuid PRIMARY KEY REFERENCES auth.users,
    commission_discount_rate numeric NOT NULL DEFAULT 1.0,
    extra                   jsonb   -- future settings fields
);
```

---

## Data Migration

A one-time script `scripts/migrate_csv.py` bulk-imports the existing CSVs for the first user:

1. Sign in as the owner via Supabase Auth to get `user_id`
2. Read `transactions.csv`, `cashflow.csv`, `stocks.csv`, `settings.json`
3. Insert rows into Postgres with `user_id`

Original CSV files are kept as backup and can be removed after verification.

---

## Backend Changes

| File | Change |
|------|--------|
| `config.py` | Add `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET` from env |
| `services/csv_service.py` | Replaced by `services/supabase_service.py` (same interface) |
| `routers/deps.py` | Add `get_current_user` dependency; keep `get_supabase_service` |
| All routers | Add `user_id: str = Depends(get_current_user)`, pass to service |
| `requirements.txt` | Add `supabase`, `python-jose[cryptography]`, `python-dotenv` |

Business logic in `services/calculator.py` and all computation in routers is unchanged.

---

## Excel Export

New endpoint added to the settings router:

**`GET /api/export`** — auth-protected, scoped to `user_id`

1. Fetch user's transactions and cashflow from Supabase
2. Build in-memory `.xlsx` with `openpyxl` (already a dependency):
   - Sheet 1 `交易紀錄`: date, action, code, name, trade_type, buy_shares, buy_price, sell_shares, sell_price, dividend_income, reason
   - Sheet 2 `出入金`: date, deposit, withdrawal, principal_snapshot
3. Return as `StreamingResponse` with `Content-Disposition: attachment; filename="stocker_export.xlsx"`

Frontend: "匯出 Excel" button in settings page triggers a browser download via `fetch` + `Blob`.

---

## Frontend Changes

| Area | Change |
|------|--------|
| New login/signup page | Email/password form using Supabase JS client |
| Auth context / store | Hold session + auto-refresh JWT |
| API client (axios/fetch) | Attach `Authorization: Bearer <token>` header globally |
| Settings page | Add "匯出 Excel" download button |
| Route guard | Redirect unauthenticated users to login |

---

## Open Questions

_None — all resolved during design session._
