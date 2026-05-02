# Admin Console V1

## Summary

Build a backend-gated admin console for Stocker that is available only to allowlisted admin emails. Add a placeholder app-level admin capability check, show an “Open Admin” button on the existing settings page when the signed-in user is an admin, and add a new read-heavy `/admin` page for curated table browsing, analytics, user stats, and bounded app-managed configuration edits.

## Key Changes

- **Admin identity and access**

  - Add backend config for an admin email allowlist, e.g. `ADMIN_EMAIL_ALLOWLIST`, parsed into normalized email values.
  - Extend auth decoding/current-user handling so backend code can access both `user_id` and `email` from the Supabase token.
  - Add a reusable admin dependency that returns `403` unless the signed-in user email is allowlisted.
  - Add a small “capabilities” response for the current user, with at least `is_admin: boolean`, as the placeholder app-level admin marker for now.
  - Keep the role source isolated behind this capability/dependency layer so it can later move from config allowlist to a DB-backed admin table without changing frontend behavior.
- **Backend admin API**

  - Add a new admin router under `/api/admin`.
  - Add `GET /api/admin/capabilities` or fold capabilities into a general `/api/me` endpoint; frontend only needs `is_admin`.
  - Add `GET /api/admin/overview` for dashboard metrics such as total users, recent sign-ins/users created if available, per-table row counts, and basic app activity counts derived from current app tables.
  - Add `GET /api/admin/tables` to return a curated list of browsable tables and display metadata.
  - Add `GET /api/admin/tables/{table_name}` with pagination for read-only browsing of allowed tables only.
  - Add app-managed config endpoints, e.g. `GET /api/admin/config` and `PUT /api/admin/config`, backed by a dedicated Stocker-owned config store rather than raw Supabase project settings.
  - Do not add arbitrary row create/update/delete, schema management, or generic SQL execution.
- **Data model and service layer**

  - Add a dedicated app config table/migration for bounded admin-editable settings, with a narrow schema owned by the app.
  - Add service methods for:
    - resolving admin capability from current user email
    - fetching curated table metadata
    - reading paginated rows from allowed tables
    - computing overview analytics/user stats
    - reading/updating app config
  - Keep the existing `SupabaseService` user-scoped behavior unchanged for normal app routes; add a separate admin-oriented service path if that keeps responsibilities cleaner.
- **Frontend**

  - Add an admin capability query/hook that runs for authenticated users.
  - Update [`frontend/src/pages/Settings.tsx`](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Settings.tsx) to show an “Open Admin” button only when `is_admin` is true.
  - Add a new `/admin` route and page component.
  - Guard `/admin` in the frontend using the capability result; non-admins should be redirected away or shown a forbidden state, while backend remains the source of truth.
  - Build the admin page with three sections:
    - overview cards for analytics and user stats
    - a read-only table browser with table selector, pagination, and row detail display
    - a bounded app-config editor for the modeled config values
  - Keep the main nav unchanged; no admin nav item in v1.

## Public Interfaces / Types

- Backend config: add `ADMIN_EMAIL_ALLOWLIST`.
- Auth/deps: replace plain current-user string usage with a structured current-user model containing at least `id` and `email`.
- New response models:
  - `CurrentUserCapabilities { is_admin: bool }`
  - `AdminOverview`
  - `AdminTableSummary`
  - `AdminTablePage`
  - `AdminAppConfig`
- Frontend API/types/hooks: add matching TS types and queries for capabilities, admin overview, admin tables, admin table page, and admin config.

## Test Plan

- Backend tests
  - allowlisted email returns `is_admin: true`; non-allowlisted email returns `false`
  - admin dependency rejects non-admin users with `403`
  - admin overview endpoint returns expected analytics shape
  - table browser only allows curated tables and paginates results
  - config read/update endpoints work for admins and reject non-admins
  - existing non-admin routes still behave unchanged
- Frontend tests
  - settings page shows the admin button only for admin users
  - `/admin` route renders for admins and blocks non-admins
  - admin page loads overview metrics, browsable tables, and config form
  - read-only browser does not expose edit/delete actions
  - config save issues the expected API call and updates UI state

## Assumptions

- Admin membership source for v1 is backend email allowlist only.
- The Supabase JWT/session payload includes the user email needed for allowlist checks; if missing, the user is treated as non-admin.
- “Configuration-like changes” means editing only Stocker-owned modeled config values stored in app tables, not Supabase project settings.
- Table browsing is limited to a curated allowlist of app tables, not every table in the database.
