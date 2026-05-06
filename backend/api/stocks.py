from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_ledger_store, get_price_service, get_stock_catalog
from backend.config import get_settings
from backend.domain.ledger.interfaces import LedgerStore, StockCatalog
from backend.domain.portfolio.calculator import calculate_trade_financials
from backend.domain.portfolio.price_service import PriceService
from backend.models.domain.ledger import TradeFinancials
from backend.models.domain.portfolio import PriceQuote, StockLookup


router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/search", response_model=list[StockLookup])
def search_stocks(
    q: str = "",
    stock_catalog: StockCatalog = Depends(get_stock_catalog),
):
    return stock_catalog.search_stocks(q)


@router.get("/prices", response_model=list[PriceQuote])
async def get_prices(
    codes: str = Query(default=""),
    stock_catalog: StockCatalog = Depends(get_stock_catalog),
    prices: PriceService = Depends(get_price_service),
):
    max_codes = get_settings().price_lookup_max_codes
    normalized_codes = list(dict.fromkeys(code.strip() for code in codes.split(",") if code.strip()))
    if len(normalized_codes) > max_codes:
        raise HTTPException(
            status_code=400,
            detail=f"A maximum of {max_codes} stock codes may be requested at once",
        )
    return await prices.get_prices(normalized_codes, stock_catalog.read_stocks())


@router.get("/preview-fee", response_model=TradeFinancials)
def preview_fee(
    action: str,
    amount: float,
    code: str | None = None,
    shares: float | None = None,
    trade_type: str = "一般",
    ledger_store: LedgerStore = Depends(get_ledger_store),
):
    return calculate_trade_financials(
        action=action,
        trade_type=trade_type,
        code=code,
        shares=shares,
        amount=amount,
        settings=ledger_store.get_settings(),
    )
