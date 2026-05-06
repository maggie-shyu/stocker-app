from fastapi import APIRouter, Depends

from backend.api.deps import get_ledger_store, get_price_service, get_stock_catalog
from backend.domain.ledger.interfaces import LedgerStore, StockCatalog
from backend.domain.portfolio.price_service import PriceService
from backend.domain.portfolio.read_module import read_holdings
from backend.models.domain.portfolio import Holding


router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.get("", response_model=list[Holding])
async def list_holdings(
    ledger_store: LedgerStore = Depends(get_ledger_store),
    stock_catalog: StockCatalog = Depends(get_stock_catalog),
    prices: PriceService = Depends(get_price_service),
):
    return await read_holdings(ledger_store, stock_catalog, prices)
