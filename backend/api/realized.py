from datetime import date

from fastapi import APIRouter, Depends

from backend.api.deps import get_ledger_store
from backend.domain.ledger.interfaces import LedgerStore
from backend.domain.portfolio.read_module import read_realized
from backend.models.api.portfolio import RealizedResponse


router = APIRouter(prefix="/api/realized", tags=["realized"])


@router.get("", response_model=RealizedResponse)
def list_realized(
    code: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    ledger_store: LedgerStore = Depends(get_ledger_store),
):
    return read_realized(ledger_store, code=code, from_date=from_date, to_date=to_date)
