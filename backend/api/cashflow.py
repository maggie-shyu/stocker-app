from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_ledger_store
from backend.domain.ledger.interfaces import LedgerStore
from backend.models.api.ledger import CashflowCreate
from backend.models.domain.ledger import CashflowRecord


router = APIRouter(prefix="/api/cashflow", tags=["cashflow"])


@router.get("", response_model=list[CashflowRecord])
def list_cashflows(ledger_store: LedgerStore = Depends(get_ledger_store)):
    return ledger_store.read_cashflows()


@router.post("", response_model=CashflowRecord)
def create_cashflow(
    payload: CashflowCreate,
    ledger_store: LedgerStore = Depends(get_ledger_store),
):
    return ledger_store.append_cashflow(payload)


@router.put("/{cf_id}", response_model=CashflowRecord)
def update_cashflow(
    cf_id: str,
    payload: CashflowCreate,
    ledger_store: LedgerStore = Depends(get_ledger_store),
):
    try:
        return ledger_store.update_cashflow(cf_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Cashflow not found") from exc


@router.delete("/{cf_id}", status_code=204)
def delete_cashflow(
    cf_id: str,
    ledger_store: LedgerStore = Depends(get_ledger_store),
):
    try:
        ledger_store.delete_cashflow(cf_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Cashflow not found") from exc
    return None
