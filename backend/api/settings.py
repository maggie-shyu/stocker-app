from fastapi import APIRouter, Depends

from backend.api.deps import get_ledger_store
from backend.domain.ledger.interfaces import LedgerStore
from backend.models.domain.ledger import UserSettings


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=UserSettings)
def read_settings(ledger_store: LedgerStore = Depends(get_ledger_store)):
    return ledger_store.get_settings()


@router.put("", response_model=UserSettings)
def update_settings(
    payload: UserSettings,
    ledger_store: LedgerStore = Depends(get_ledger_store),
):
    return ledger_store.update_settings(payload)
