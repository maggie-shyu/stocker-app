from fastapi import APIRouter, Depends, Query

from models.schemas import PriceQuote, StockLookup, TradeFinancials
from routers.deps import get_price_service, get_supabase_service
from services.calculator import calculate_trade_financials
from services.price_service import PriceService
from services.supabase_service import SupabaseService


router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/search", response_model=list[StockLookup])
def search_stocks(
    q: str = "",
    service: SupabaseService = Depends(get_supabase_service),
):
    return service.search_stocks(q)


@router.get("/prices", response_model=list[PriceQuote])
async def get_prices(
    codes: str = Query(default=""),
    service: SupabaseService = Depends(get_supabase_service),
    prices: PriceService = Depends(get_price_service),
):
    return await prices.get_prices(codes.split(","), service.read_stocks())


@router.get("/preview-fee", response_model=TradeFinancials)
def preview_fee(
    action: str,
    amount: float,
    code: str | None = None,
    shares: float | None = None,
    trade_type: str = "一般",
    service: SupabaseService = Depends(get_supabase_service),
):
    return calculate_trade_financials(
        action=action,
        trade_type=trade_type,
        code=code,
        shares=shares,
        amount=amount,
        discount_rate=service.get_commission_discount_rate(),
    )
