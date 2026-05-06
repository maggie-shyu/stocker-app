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

## Testing

- Integration tests live in `backend/tests/integration/`.
- Unit tests live in `backend/tests/unit/`.
- Shared fixtures and helpers live in `backend/tests/support/`.
