# Stocker

Stocker is a personal stock portfolio tracker with a React frontend, a FastAPI backend, and Supabase for authentication and persistence.

## What

Stocker tracks portfolio holdings, transactions, realized results, and admin workflows in one app.

## Setup

Create and activate a Python environment, then install the backend and frontend dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
make backend-install
make frontend-install
touch backend/.env frontend/.env
```

Populate `backend/.env` and `frontend/.env` with the required Supabase credentials before starting the app.

## Usage

Start both apps, then hit the health check:

```bash
make backend-dev
make frontend-dev
curl http://127.0.0.1:8000/api/health
```

## Structure

- `backend/`: FastAPI routes, domain logic, infrastructure adapters, and tests
- `frontend/src/app/`: app shell, routing, and entrypoint wiring
- `frontend/src/features/`: feature-specific pages, hooks, queries, and types
- `frontend/src/platform/`: API client, auth, and browser utilities
- `frontend/src/shared/`: reusable UI components and utilities
- `supabase/`: SQL migrations and local Supabase metadata

## Architecture Notes

- [Backend architecture](.context/backend-architecture.md)
- [Frontend architecture](.context/frontend-architecture.md)
