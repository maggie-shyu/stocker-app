# Frontend Architecture

The frontend is split into app wiring, feature modules, platform adapters, and shared building blocks.

## Layers

- `frontend/src/app/` holds the entrypoint, router setup, and app shell wiring.
- `frontend/src/features/` holds feature-local pages, hooks, queries, and types.
- `frontend/src/platform/` holds integrations such as the Supabase client, auth session helpers, API client code, and browser utilities.
- `frontend/src/shared/` holds reusable UI components and generic utilities.

## Data Flow

- App composition starts in `frontend/src/app/main.tsx` and `frontend/src/app/App.tsx`.
- Feature pages consume feature-local query modules rather than a shared app-wide API barrel.
- Auth state is routed through `frontend/src/platform/auth/session.ts` and the auth context in `frontend/src/features/auth/`.

## Testing

- App shell coverage lives in `frontend/src/app/App.test.tsx`.
- Feature tests live next to their feature modules.
- Browser helper tests live in `frontend/src/platform/browser/`.
