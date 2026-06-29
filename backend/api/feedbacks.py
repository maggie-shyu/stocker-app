from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_ledger_store
from backend.domain.ledger.interfaces import LedgerStore
from backend.models.api.ledger import FeedbackCreate
from backend.models.domain.ledger import FeedbackRecord


router = APIRouter(prefix="/api/feedbacks", tags=["feedbacks"])


@router.get("", response_model=list[FeedbackRecord])
def list_feedbacks(ledger_store: LedgerStore = Depends(get_ledger_store)):
    return ledger_store.read_feedbacks()


@router.post("", response_model=FeedbackRecord)
def create_feedback(
    payload: FeedbackCreate,
    ledger_store: LedgerStore = Depends(get_ledger_store),
):
    return ledger_store.append_feedback(payload)


@router.put("/{feedback_id}", response_model=FeedbackRecord)
def update_feedback(
    feedback_id: str,
    payload: FeedbackCreate,
    ledger_store: LedgerStore = Depends(get_ledger_store),
):
    try:
        return ledger_store.update_feedback(feedback_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Feedback not found") from exc


@router.delete("/{feedback_id}", status_code=204)
def delete_feedback(
    feedback_id: str,
    ledger_store: LedgerStore = Depends(get_ledger_store),
):
    try:
        ledger_store.delete_feedback(feedback_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Feedback not found") from exc
    return None
