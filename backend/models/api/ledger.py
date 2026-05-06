from datetime import date

from pydantic import BaseModel

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
    dividend_income: float | None = None
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
