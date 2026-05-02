# Add admin page access

> As this is a personal project for now, I will use my account as the admin account for supabase management and other admin-level operations, but I want it to be able to easily changed to other admin account in future.
>
> Leave a placeholder for me to mark my account as an app‑level admin. Add a button in the settings page to open the admin page if the user is marked as admin.
>
> Create an admin page for supabase management to view all tables and data; see dashboards with analytics and user stats; make configuration‑like changes.

<details><summary>10 previous messages</summary>

> I’m grounding in the repo first so we can turn this into a decision-complete plan. I’ll inspect the existing auth, settings page, and any Supabase/admin structure before I ask you to choose between tradeoffs.
>
> <details><summary>Explored 3 files</summary>
>
> - Read `~/workspace/harness/skills/superpowers/using-superpowers/SKILL.md`
> - Read `~/workspace/harness/skills/superpowers/brainstorming/SKILL.md`
> - Read `~/workspace/harness/skills/superpowers/writing-plans/SKILL.md`
>
> </details>
>
> I’m using the `brainstorming` skill to shape the feature design before any implementation. Next I’m checking the current app structure, auth flow, settings page, and any Supabase admin groundwork so the plan fits what’s already there.
>
> <details><summary>Explored 1 search, 1 list, ran 2 commands</summary>
>
> - Ran `pwd`
>
> <details><summary>Explored 1 search, 1 list</summary>
>
> - Listed files
> - Searched for `supabase|settings|admin|profile|role|auth` in `.`
>
> </details>
>
> - Ran `git log --oneline -5`
>
> </details>
>
> I found a pretty lean setup: React routes already include `/settings`, auth is Supabase-backed, and the backend currently scopes everything to the signed-in user through RLS-aware service calls. I’m reading the actual settings/auth/router code now so the plan can account for how an app-level admin flag should flow end to end.
>
> <details><summary>Explored 7 files</summary>
>
> - Read `./frontend/src/pages/Settings.tsx`
> - Read `./frontend/src/contexts/AuthContext.tsx`
> - Read `./frontend/src/App.tsx`
> - Read `./backend/routers/settings.py`
> - Read `./frontend/src/components/layout/AppShell.tsx`
> - Read `./backend/models/schemas.py`
> - Read `./backend/routers/deps.py`
>
> </details>
>
> The current model has a single `user_settings` row per user and no concept of app roles yet, which means we’ll need to introduce a small admin-capability layer rather than piggyback on existing settings alone. I’m checking the service and tests next to see the cleanest place to expose that without breaking the current user-scoped behavior.
>
> <details><summary>Explored 5 files, 1 search, 1 list</summary>
>
> - Read `./backend/services/supabase_service.py`
> - Read `./backend/tests/test_api.py`
> - Read `./backend/tests/test_api.py`
> - Read `./frontend/src/api/types.ts`
> - Read `./frontend/src/App.test.tsx`
> - Listed files in `frontend`
> - Searched for `supabase|lib`
>
> </details>
>
> I’ve confirmed the frontend tests already mock auth and API cleanly, so adding an admin affordance can fit the existing testing style without a huge test harness change. One gap I’m verifying now is where the Supabase browser client lives, because that will shape whether the admin page should read directly from Supabase or go through new backend endpoints.
>
> <details><summary>Explored 6 files, 1 list</summary>
>
> - Listed files in `frontend`
> - Read `./frontend/src/api/client.ts`
> - Read `./README.md`
> - Read `./frontend/src/hooks/queries.ts`
> - Read `./frontend/src/components/RouteGuard.tsx`
> - Read `./frontend/src/api/query.ts`
> - Read `./frontend/src/lib/supabase.ts`
>
> </details>

</details>

Some of what we're working on might be easier to explain if I can show it to you in a web browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. This feature is still new and can be token-intensive. Want to try it? (Requires opening a local URL)

> No, I don't want to try this token-intensive feature. What are you unclear about that I might help you (answer you)?

<details><summary>3 previous messages</summary>

> I’ve cleared most of the repo-level unknowns. The main product decision left is how powerful this first admin page should be, because the codebase currently has no app-level admin role or unrestricted data API yet.
>
> That helps narrow it a lot. One more decision will lock the role design cleanly: where should the app-level admin flag live for now so it’s easy to reassign later?
>
> One last scope choice would keep the admin plan from growing into a full settings builder. When you say “configuration-like changes,” what should v1 actually allow an admin to change from the app?

</details>

The remaining choices are clear enough now, so here are the strongest ways to shape it.

1. Recommended: app-owned admin console with backend-gated access.
   It would use an email allowlist in backend config for who counts as admin, show the admin entry/button only when the signed-in user’s email matches, and keep all admin data access behind new backend endpoints. The admin page would let you browse tables/data, see analytics and user stats, and make a bounded set of app-managed changes plus selected row edits. This fits the current architecture best, keeps the service key on the backend, and still leaves a clean placeholder to move from config-based admin assignment to a database-backed role later.
2. Frontend-driven Supabase console.
   The admin page would talk more directly to Supabase from the browser for table browsing and editing. It would feel closer to “mini Supabase Studio,” but it clashes with the current app shape, would be harder to secure safely with the existing publishable-key client, and would likely force more RLS and policy complexity up front.
3. Thin admin launcher plus external tooling.
   The app would only detect admin users, show the admin button, and provide a lightweight dashboard with links or embedded views for external Supabase management. This is the smallest change, but it doesn’t really satisfy your request for in-app table browsing, analytics, and configuration-style edits.

My recommendation is option 1: backend-gated admin console. It gives you the admin experience inside Stocker without exposing Supabase management power to the browser.

Does that direction look right so far?

> I'll choose option 1: app-owned admin console with backend-gated access.
> It would use an email allowlist in backend config for who counts as admin, show the admin entry/button only when the signed-in user’s email matches, and keep all admin data access behind new backend endpoints. The admin page would let you browse tables/data, see analytics and user stats, and make a bounded set of app-managed changes.
>
> I don't want the admin page to support supabase table edits for now.

<details><summary>1 previous message</summary>

> That narrows the shape nicely. I have the backend security model and scope locked; the last meaningful UI decision is whether the admin page should be reachable only from `設定`, or also appear as a first-class navigation item for admins.

</details>

Here’s the design I’d propose for this first admin feature.

**Access Model**

Admin status will be determined on the backend from a configured email allowlist, not from the browser and not from a mutable table yet. The frontend will ask the backend for the current user’s capabilities, and only if the backend says `is_admin: true` will `設定` show an “Open Admin” button and allow access to the admin route. This keeps the service key and all privileged Supabase access on the server while leaving a clean future swap point from config-based admin membership to a DB-backed role model.

**Admin Surface**

The new admin page will be a read-heavy internal console with three areas:

1. table/data browser for a curated list of app tables, with pagination and read-only row inspection
2. analytics dashboard for system-level metrics like user counts, recent activity, and record totals
3. bounded app-managed configuration controls for a small modeled config set owned by Stocker, not raw Supabase project settings

It will not support arbitrary table edits, deletes, schema changes, or direct Supabase project management in v1.

**Backend Shape**

The backend will gain an admin-capabilities endpoint for the signed-in user plus a small admin router protected by an explicit admin dependency. That router will use privileged Supabase access to read across users and tables, aggregate analytics, and read/write only the modeled app config records. Existing user-scoped routes stay unchanged. The new admin dependency becomes the single enforcement point so future role-source changes do not require rewriting every admin endpoint.

**Frontend Shape**

The frontend will add:

- an auth-adjacent capability fetch so the app knows whether the current user is admin
- a new `/admin` page guarded by both login state and admin status
- an admin launch button in `設定` shown only for admins
- a read-only admin UI with summary cards, a table selector, paginated data grid/details, and a small config form section

If a non-admin somehow visits `/admin`, the UI should redirect away or show a forbidden state based on the backend response, rather than rendering partial admin data.

**Failure Handling And Testing**

If the allowlist is empty or the signed-in user email is unavailable, the app should treat the user as non-admin. Admin endpoints return `403` for non-admins and never leak privileged data shape beyond that. Tests should cover allowlisted vs non-allowlisted users, conditional rendering of the settings button, `/admin` route protection, analytics payloads, read-only table browsing, and bounded config updates.

Does this design look right so far?

> Yes

<details><summary>1 previous message</summary>

> Plan
>
> # Admin Console V1
>
> ## Summary
>
> Build a backend-gated admin console for Stocker that is available only to allowlisted admin emails. Add a placeholder app-level admin capability check, show an “Open Admin” button on the existing settings page when the signed-in user is an admin, and add a new read-heavy `/admin` page for curated table browsing, analytics, user stats, and bounded app-managed configuration edits.
>
> ## Key Changes
>
> - **Admin identity and access**
>
>   - Add backend config for an admin email allowlist, e.g. `ADMIN_EMAIL_ALLOWLIST`, parsed into normalized email values.
>   - Extend auth decoding/current-user handling so backend code can access both `user_id` and `email` from the Supabase token.
>   - Add a reusable admin dependency that returns `403` unless the signed-in user email is allowlisted.
>   - Add a small “capabilities” response for the current user, with at least `is_admin: boolean`, as the placeholder app-level admin marker for now.
>   - Keep the role source isolated behind this capability/dependency layer so it can later move from config allowlist to a DB-backed admin table without changing frontend behavior.
> - **Backend admin API**
>
>   - Add a new admin router under `/api/admin`.
>   - Add `GET /api/admin/capabilities` or fold capabilities into a general `/api/me` endpoint; frontend only needs `is_admin`.
>   - Add `GET /api/admin/overview` for dashboard metrics such as total users, recent sign-ins/users created if available, per-table row counts, and basic app activity counts derived from current app tables.
>   - Add `GET /api/admin/tables` to return a curated list of browsable tables and display metadata.
>   - Add `GET /api/admin/tables/{table_name}` with pagination for read-only browsing of allowed tables only.
>   - Add app-managed config endpoints, e.g. `GET /api/admin/config` and `PUT /api/admin/config`, backed by a dedicated Stocker-owned config store rather than raw Supabase project settings.
>   - Do not add arbitrary row create/update/delete, schema management, or generic SQL execution.
> - **Data model and service layer**
>
>   - Add a dedicated app config table/migration for bounded admin-editable settings, with a narrow schema owned by the app.
>   - Add service methods for:
>     - resolving admin capability from current user email
>     - fetching curated table metadata
>     - reading paginated rows from allowed tables
>     - computing overview analytics/user stats
>     - reading/updating app config
>   - Keep the existing `SupabaseService` user-scoped behavior unchanged for normal app routes; add a separate admin-oriented service path if that keeps responsibilities cleaner.
> - **Frontend**
>
>   - Add an admin capability query/hook that runs for authenticated users.
>   - Update [`frontend/src/pages/Settings.tsx`](/Users/meimei/workspace/ntu/repo/stocker/frontend/src/pages/Settings.tsx) to show an “Open Admin” button only when `is_admin` is true.
>   - Add a new `/admin` route and page component.
>   - Guard `/admin` in the frontend using the capability result; non-admins should be redirected away or shown a forbidden state, while backend remains the source of truth.
>   - Build the admin page with three sections:
>     - overview cards for analytics and user stats
>     - a read-only table browser with table selector, pagination, and row detail display
>     - a bounded app-config editor for the modeled config values
>   - Keep the main nav unchanged; no admin nav item in v1.
>
> ## Public Interfaces / Types
>
> - Backend config: add `ADMIN_EMAIL_ALLOWLIST`.
> - Auth/deps: replace plain current-user string usage with a structured current-user model containing at least `id` and `email`.
> - New response models:
>   - `CurrentUserCapabilities { is_admin: bool }`
>   - `AdminOverview`
>   - `AdminTableSummary`
>   - `AdminTablePage`
>   - `AdminAppConfig`
> - Frontend API/types/hooks: add matching TS types and queries for capabilities, admin overview, admin tables, admin table page, and admin config.
>
> ## Test Plan
>
> - Backend tests
>   - allowlisted email returns `is_admin: true`; non-allowlisted email returns `false`
>   - admin dependency rejects non-admin users with `403`
>   - admin overview endpoint returns expected analytics shape
>   - table browser only allows curated tables and paginates results
>   - config read/update endpoints work for admins and reject non-admins
>   - existing non-admin routes still behave unchanged
> - Frontend tests
>   - settings page shows the admin button only for admin users
>   - `/admin` route renders for admins and blocks non-admins
>   - admin page loads overview metrics, browsable tables, and config form
>   - read-only browser does not expose edit/delete actions
>   - config save issues the expected API call and updates UI state
>
> ## Assumptions
>
> - Admin membership source for v1 is backend email allowlist only.
> - The Supabase JWT/session payload includes the user email needed for allowlist checks; if missing, the user is treated as non-admin.
> - “Configuration-like changes” means editing only Stocker-owned modeled config values stored in app tables, not Supabase project settings.
> - Table browsing is limited to a curated allowlist of app tables, not every table in the database.

</details>
