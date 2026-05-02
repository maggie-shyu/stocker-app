# Stocker

Stocker is a personal stock portfolio tracker with a React frontend, a FastAPI backend, and Supabase for authentication and persistence.

## Project Layout

- `frontend/`: Vite + React application
- `backend/`: FastAPI API, domain logic, and tests
- `supabase/`: SQL migrations and local Supabase metadata

## Stack

- Frontend: React, TypeScript, Vite, React Query, Supabase JS
- Backend: FastAPI, Pydantic, Supabase Python client
- Data/Auth: Supabase

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm

## Environment

Create these local files before running the app:

- `backend/.env`
- `frontend/.env`

Backend variables:

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_KEY`
- `SUPABASE_LEGACY_JWT_SECRET` or `SUPABASE_JWT_SECRET`
- `ADMIN_EMAIL_ALLOWLIST` comma-separated emails allowed to open the app admin console

Frontend variables:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`

## Setup

Install backend dependencies from the repo root:

```bash
pip install -e .[dev]
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

## Run Locally

Start the backend from the repo root:

```bash
uvicorn backend.main:app --reload
```

Start the frontend:

```bash
cd frontend
npm run dev
```

## Common Commands

From the repo root:

```bash
make backend-test
make frontend-test
make frontend-build
```

You can also run commands directly:

```bash
pytest
cd frontend && npm test
cd frontend && npm run build
```

## API Notes

- Health check: `GET /api/health`
- Main API routes are mounted under `/api`
- Excel import and export live under `/api/export`

## Testing

- Backend tests live in `backend/tests/`
- Frontend tests live next to app code in `frontend/src/`
- Test CSV fixtures used by backend tests live in `backend/tests/data/`

## Migrations

Supabase schema migrations live in `supabase/migrations/`.

## Conventions

- Run backend tools from the repo root so `backend` is treated as the package root.
- Keep generated files out of git.
- Put test-only helpers under `backend/tests/` rather than `backend/services/`.
- Prefer updating shared repo config in one place when adding new tools or workflows.
