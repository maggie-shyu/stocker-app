from fastapi import APIRouter, Depends, HTTPException

from backend.models.schemas import CashflowCreate, CashflowRecord
from backend.routers.deps import get_supabase_service
from backend.services.supabase_service import SupabaseService


router = APIRouter(prefix="/api/cashflow", tags=["cashflow"])


@router.get("", response_model=list[CashflowRecord])
def list_cashflows(service: SupabaseService = Depends(get_supabase_service)):
    return service.read_cashflows()


@router.post("", response_model=CashflowRecord)
def create_cashflow(
    payload: CashflowCreate,
    service: SupabaseService = Depends(get_supabase_service),
):
    return service.append_cashflow(payload)


@router.put("/{cf_id}", response_model=CashflowRecord)
def update_cashflow(
    cf_id: str,
    payload: CashflowCreate,
    service: SupabaseService = Depends(get_supabase_service),
):
    try:
        return service.update_cashflow(cf_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Cashflow not found") from exc


@router.delete("/{cf_id}", status_code=204)
def delete_cashflow(
    cf_id: str,
    service: SupabaseService = Depends(get_supabase_service),
):
    try:
        service.delete_cashflow(cf_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Cashflow not found") from exc
    return None
