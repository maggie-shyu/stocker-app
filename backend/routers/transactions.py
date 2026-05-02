from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.models.schemas import TransactionCreate, TransactionPage, TransactionRecord
from backend.routers.deps import get_price_service, get_supabase_service
from backend.services.price_service import PriceService
from backend.services.supabase_service import SupabaseService


router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=TransactionPage)
def list_transactions(
    action: str | None = None,
    code: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    service: SupabaseService = Depends(get_supabase_service),
):
    items = service.read_transactions()
    if action:
        items = [item for item in items if item.action == action]
    if code:
        items = [item for item in items if item.code == code]
    if from_date:
        items = [item for item in items if item.date >= from_date]
    if to_date:
        items = [item for item in items if item.date <= to_date]

    total = len(items)
    start = (page - 1) * page_size
    return TransactionPage(
        items=items[start : start + page_size],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TransactionRecord)
async def create_transaction(
    payload: TransactionCreate,
    service: SupabaseService = Depends(get_supabase_service),
    prices: PriceService = Depends(get_price_service),
):
    current_price = 0.0
    quote = await prices.get_price(payload.code, payload.name)
    if quote.price is not None:
        current_price = quote.price
    return service.append_transaction(payload, current_price=current_price)


@router.put("/{tx_id}", response_model=TransactionRecord)
async def update_transaction(
    tx_id: str,
    payload: TransactionCreate,
    service: SupabaseService = Depends(get_supabase_service),
):
    try:
        return service.update_transaction(tx_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Transaction not found") from exc


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(
    tx_id: str,
    service: SupabaseService = Depends(get_supabase_service),
):
    try:
        service.delete_transaction(tx_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Transaction not found") from exc
    return None
