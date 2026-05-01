from fastapi import APIRouter, Depends, HTTPException

from models.schemas import CashflowCreate, CashflowRecord
from routers.deps import get_csv_service
from services.csv_service import CsvService


router = APIRouter(prefix="/api/cashflow", tags=["cashflow"])


@router.get("", response_model=list[CashflowRecord])
def list_cashflows(service: CsvService = Depends(get_csv_service)):
    return service.read_cashflows()


@router.post("", response_model=CashflowRecord)
def create_cashflow(
    payload: CashflowCreate,
    service: CsvService = Depends(get_csv_service),
):
    return service.append_cashflow(payload)


@router.put("/{row_id}", response_model=CashflowRecord)
def update_cashflow(
    row_id: int,
    payload: CashflowCreate,
    service: CsvService = Depends(get_csv_service),
):
    try:
        return service.update_cashflow(row_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Cashflow not found") from exc


@router.delete("/{row_id}", status_code=204)
def delete_cashflow(
    row_id: int,
    service: CsvService = Depends(get_csv_service),
):
    try:
        service.delete_cashflow(row_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Cashflow not found") from exc
    return None
