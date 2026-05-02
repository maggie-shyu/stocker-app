from datetime import date
from fastapi import APIRouter, Depends

from backend.models.schemas import AccountOverviewHolding, DashboardResponse, PriceStatus
from backend.routers.deps import get_price_service, get_supabase_service
from backend.services.calculator import compute_portfolio
from backend.services.price_service import PriceService
from backend.services.supabase_service import SupabaseService


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def read_dashboard(
    service: SupabaseService = Depends(get_supabase_service),
    prices: PriceService = Depends(get_price_service),
):
    transactions = service.read_transactions()
    cashflows = service.read_cashflows()
    codes = list({tx.code for tx in transactions})
    quotes = await prices.get_prices(codes, service.read_stocks())
    live = {q.code: q.price for q in quotes if q.price is not None}
    prev = {q.code: q.previous_close for q in quotes if q.previous_close is not None}
    price_status = PriceStatus(
        total=len(codes),
        priced=len(live),
        delayed=max(len(codes) - len(live), 0),
    )
    portfolio = compute_portfolio(
        transactions=transactions,
        cashflows=cashflows,
        live_prices=live,
        previous_closes=prev,
    )
    pie = [
        AccountOverviewHolding(
            code=h.code,
            name=h.name,
            market_value=h.market_value,
            weight=h.weight,
        )
        for h in portfolio.holdings
    ]

    benchmark_return_rate = None
    candidate_dates = [tx.date for tx in transactions]
    if candidate_dates:
        start_date = min(candidate_dates)
        benchmark_return_rate = await prices.get_benchmark_return_rate("0050.TW", start_date)

    return DashboardResponse(
        account_value=portfolio.account_value,
        principal=portfolio.principal,
        investment_years=portfolio.investment_years,
        stock_market_value=portfolio.stock_market_value,
        cash_balance=portfolio.cash_balance,
        unrealized_pnl=portfolio.unrealized_pnl,
        unrealized_pnl_rate=portfolio.unrealized_pnl_rate,
        realized_pnl=portfolio.realized_pnl,
        realized_pnl_rate=portfolio.realized_pnl_rate,
        account_pnl=portfolio.account_pnl,
        account_pnl_rate=portfolio.account_pnl_rate,
        annualized_return_rate=portfolio.annualized_return_rate,
        today_pnl=portfolio.today_pnl,
        today_pnl_rate=portfolio.today_pnl_rate,
        dividend_income=portfolio.dividend_income,
        benchmark_return_rate=benchmark_return_rate,
        start_date=start_date if candidate_dates else None,
        holdings_pie=pie,
        recent_transactions=transactions[-3:][::-1],
        price_status=price_status,
    )
