from fastapi import APIRouter, Depends

from models.schemas import Holding
from routers.deps import get_csv_service, get_price_service
from services.calculator import compute_portfolio
from services.csv_service import CsvService
from services.price_service import PriceService


router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.get("", response_model=list[Holding])
async def list_holdings(
    service: CsvService = Depends(get_csv_service),
    prices: PriceService = Depends(get_price_service),
):
    transactions = service.read_transactions()
    codes = list({tx.code for tx in transactions})
    quotes = await prices.get_prices(codes, service.read_stocks())
    live = {q.code: q.price for q in quotes if q.price is not None}
    return compute_portfolio(
        transactions=transactions,
        cashflows=service.read_cashflows(),
        live_prices=live,
    ).holdings
