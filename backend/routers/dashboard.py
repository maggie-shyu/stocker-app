from fastapi import APIRouter, Depends

from models.schemas import AccountOverviewHolding, DashboardResponse, PriceStatus
from routers.deps import get_csv_service, get_price_service
from services.calculator import compute_portfolio
from services.csv_service import CsvService
from services.price_service import PriceService


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def read_dashboard(
    service: CsvService = Depends(get_csv_service),
    prices: PriceService = Depends(get_price_service),
):
    transactions = service.read_transactions()
    codes = list({tx.code for tx in transactions})
    quotes = await prices.get_prices(codes, service.read_stocks())
    live = {q.code: q.price for q in quotes if q.price is not None}
    price_status = PriceStatus(
        total=len(codes),
        priced=len(live),
        delayed=max(len(codes) - len(live), 0),
    )
    portfolio = compute_portfolio(
        transactions=transactions,
        cashflows=service.read_cashflows(),
        live_prices=live,
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
        dividend_income=portfolio.dividend_income,
        holdings_pie=pie,
        recent_transactions=transactions[-3:][::-1],
        price_status=price_status,
    )
