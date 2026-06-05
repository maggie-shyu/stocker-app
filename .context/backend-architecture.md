# Backend Architecture

The backend is organized around a thin API layer, a domain layer, and concrete infrastructure adapters.

## Layers

- `backend/api/` holds FastAPI routes and dependency wiring.
- `backend/domain/` holds portfolio and ledger logic that should stay mostly framework-free.
- `backend/infrastructure/` holds external integrations such as Supabase and market-data providers.
- `backend/models/api/` contains request and response shapes.
- `backend/models/domain/` contains internal domain models used by the portfolio and ledger code.

## Data Flow

- Routes resolve dependencies in `backend/api/deps.py`.
- Portfolio reads flow through `backend/domain/portfolio/read_module.py`.
- Supabase-backed storage lives in `backend/infrastructure/supabase/`.
- Market data fetches go through `backend/infrastructure/market_data/yfinance_quote_provider.py`.

## Keep-Alive 

(for Render free tier)

- Render spins down after 15 min idle → ~30s cold start
- UptimeRobot (free) pings `GET /api/health` every 5 min to prevent spin-down
- Monitor type: **Keyword**, keyword: `ok`, condition: **start incident when keyword doesn't exist**

## Testing

- Integration tests live in `backend/tests/integration/`.
- Unit tests live in `backend/tests/unit/`.
- Shared fixtures and helpers live in `backend/tests/support/`.
