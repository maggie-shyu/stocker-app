from datetime import date

from pydantic import BaseModel, field_validator

from backend.models.domain.ledger import Action, CashflowRecord, TradeType, TransactionRecord


class TransactionCreate(BaseModel):
    date: date
    action: Action
    code: str
    name: str
    trade_type: TradeType = "一般"
    buy_shares: float | None = None
    buy_price: float | None = None
    sell_shares: float | None = None
    sell_price: float | None = None
    dividend_shares: float | None = None
    dividend_price: float | None = None
    reason: str | None = None


class TransactionPage(BaseModel):
    items: list[TransactionRecord]
    total: int
    page: int
    page_size: int


class CashflowCreate(BaseModel):
    date: date
    deposit: float = 0
    withdrawal: float = 0


class FeedbackCreate(BaseModel):
    subject: str
    body: str = ""

    @field_validator("subject")
    @classmethod
    def subject_must_not_be_empty(cls, value: str) -> str:
        subject = value.strip()
        if not subject:
            raise ValueError("Feedback subject must not be empty")
        return subject
