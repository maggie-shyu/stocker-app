from fastapi import APIRouter, Depends, HTTPException, Query

from backend.config import get_settings
from backend.models.schemas import PriceQuote, StockLookup, TradeFinancials
from backend.routers.deps import get_price_service, get_supabase_service
from backend.services.calculator import calculate_trade_financials
from backend.services.price_service import PriceService
from backend.services.supabase_service import SupabaseService


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
    max_codes = get_settings().price_lookup_max_codes
    normalized_codes = list(dict.fromkeys(code.strip() for code in codes.split(",") if code.strip()))
    if len(normalized_codes) > max_codes:
        raise HTTPException(
            status_code=400,
            detail=f"A maximum of {max_codes} stock codes may be requested at once",
        )
    return await prices.get_prices(normalized_codes, service.read_stocks())


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
        settings=service.get_settings(),
    )
