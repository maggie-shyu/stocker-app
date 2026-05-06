from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


Action = Literal["買", "賣", "股利"]
TradeType = Literal["一般", "當沖"]


class TradeFinancials(BaseModel):
    current_price: float = 0
    raw_fee: float = 0
    discounted_fee: float = 0
    tax: float = 0
    amount: float = 0
    trade_cost: float = 0
    expense: float = 0
    income: float = 0
    discount_rate: float = 0


class TransactionRecord(BaseModel):
    id: str
    date: date
    action: Action
    code: str
    name: str
    trade_type: TradeType = "一般"
    buy_shares: float | None = None
    buy_price: float | None = None
    sell_shares: float | None = None
    sell_price: float | None = None
    current_price: float = 0
    raw_fee: float = 0
    discounted_fee: float = 0
    tax: float = 0
    amount: float = 0
    trade_cost: float = 0
    expense: float = 0
    income: float = 0
    reason: str | None = None
    discount_rate: float = 0


class CashflowRecord(BaseModel):
    id: str
    date: date
    deposit: float = 0
    withdrawal: float = 0


class UserSettings(BaseModel):
    commission_discount_rate: float = Field(ge=0, le=1, default=1.0)
    base_commission_rate: float = Field(ge=0, default=0.001425)
    minimum_fee: float = Field(ge=0, default=20.0)
    odd_lot_minimum_fee: float = Field(ge=0, default=1.0)
    stock_tax_rate: float = Field(ge=0, default=0.003)
    day_trade_tax_rate: float = Field(ge=0, default=0.0015)
    etf_tax_rate: float = Field(ge=0, default=0.001)
    bond_etf_tax_rate: float = Field(ge=0, default=0.0)
