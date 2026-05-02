from datetime import date

from fastapi import APIRouter, Depends

from models.schemas import DividendIncomeByStock, RealizedResponse
from routers.deps import get_supabase_service
from services.calculator import compute_portfolio, summarize_realized
from services.supabase_service import SupabaseService


router = APIRouter(prefix="/api/realized", tags=["realized"])


@router.get("", response_model=RealizedResponse)
def list_realized(
    code: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    service: SupabaseService = Depends(get_supabase_service),
):
    transactions = service.read_transactions()
    portfolio = compute_portfolio(
        transactions=transactions,
        cashflows=service.read_cashflows(),
    )
    items = portfolio.realized_trades
    if code:
        items = [item for item in items if item.code == code]
    if from_date:
        items = [item for item in items if item.date >= from_date]
    if to_date:
        items = [item for item in items if item.date <= to_date]
    last_sell_by_code = {
        item.code: item.date
        for item in sorted(items, key=lambda item: (item.code, item.date))
    }
    dividend_by_stock_map: dict[str, DividendIncomeByStock] = {}
    dividend_income = 0.0
    for tx in transactions:
        if tx.action != "股利":
            continue
        last_sell_date = last_sell_by_code.get(tx.code)
        if last_sell_date is None:
            continue
        if tx.date > last_sell_date:
            continue
        if code and tx.code != code:
            continue
        if from_date and tx.date < from_date:
            continue
        if to_date and tx.date > to_date:
            continue
        dividend_income += float(tx.income or 0)
        current = dividend_by_stock_map.get(tx.code)
        if current:
            current.dividend_income += float(tx.income or 0)
            continue
        dividend_by_stock_map[tx.code] = DividendIncomeByStock(
            code=tx.code,
            name=tx.name,
            dividend_income=float(tx.income or 0),
        )
    dividend_by_stock = sorted(dividend_by_stock_map.values(), key=lambda item: item.dividend_income, reverse=True)
    return summarize_realized(items, dividend_income=dividend_income, dividend_by_stock=dividend_by_stock)
