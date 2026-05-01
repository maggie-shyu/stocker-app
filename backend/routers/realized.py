from datetime import date

from fastapi import APIRouter, Depends

from models.schemas import RealizedResponse
from routers.deps import get_csv_service
from services.calculator import compute_portfolio, summarize_realized
from services.csv_service import CsvService


router = APIRouter(prefix="/api/realized", tags=["realized"])


@router.get("", response_model=RealizedResponse)
def list_realized(
    code: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    service: CsvService = Depends(get_csv_service),
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
    dividend_income = sum(
        float(tx.income or 0)
        for tx in transactions
        if tx.action == "股利"
        and (not code or tx.code == code)
        and (not from_date or tx.date >= from_date)
        and (not to_date or tx.date <= to_date)
    )
    return summarize_realized(items, dividend_income=dividend_income)
