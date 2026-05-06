from fastapi import APIRouter, Depends

from backend.domain.portfolio.read_module import read_dashboard as build_dashboard_response
from backend.domain.portfolio.price_service import PriceService
from backend.api.deps import get_ledger_store, get_price_service, get_stock_catalog
from backend.domain.ledger.interfaces import LedgerStore, StockCatalog
from backend.models.api.portfolio import DashboardResponse


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def read_dashboard(
    ledger_store: LedgerStore = Depends(get_ledger_store),
    stock_catalog: StockCatalog = Depends(get_stock_catalog),
    prices: PriceService = Depends(get_price_service),
):
    return await build_dashboard_response(ledger_store, stock_catalog, prices)
