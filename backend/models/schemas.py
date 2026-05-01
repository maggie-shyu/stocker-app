from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


Action = Literal["買", "賣", "股利"]
TradeType = Literal["一般", "當沖"]


class StockLookup(BaseModel):
    code: str
    name: str


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
    id: int
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


class CashflowRecord(BaseModel):
    id: int
    date: date
    deposit: float = 0
    withdrawal: float = 0
    principal_snapshot: float | None = None


class CashflowCreate(BaseModel):
    date: date
    deposit: float = 0
    withdrawal: float = 0
    is_principal: bool = False


class CommissionSettings(BaseModel):
    commission_discount_rate: float = Field(ge=0, le=1)


class AccountOverviewHolding(BaseModel):
    code: str | None = None
    name: str
    pnl_rate: float | None = None
    market_value: float = 0
    weight: float = 0


class AccountOverview(BaseModel):
    account_value: float
    account_pnl: float
    account_pnl_rate: float
    stock_market_value: float
    cash_balance: float
    holdings: list[AccountOverviewHolding]


class HoldingLot(BaseModel):
    date: date
    shares: float
    cost_per_share: float
    cost_basis: float


class Holding(BaseModel):
    code: str
    name: str
    lots: list[HoldingLot]
    total_shares: float
    avg_cost: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_rate: float
    weight: float


class RealizedTrade(BaseModel):
    date: date
    code: str
    name: str
    shares: float
    income: float
    cost_basis: float
    realized_pnl: float
    realized_pnl_rate: float
    reason: str | None = None


class RealizedResponse(BaseModel):
    items: list[RealizedTrade]
    total_realized_pnl: float
    dividend_income: float
    invested_capital: float
    realized_pnl_rate: float
    dividend_realized_pnl_rate: float
    win_rate: float
    avg_win: float
    avg_loss: float


class PortfolioSnapshot(BaseModel):
    holdings: list[Holding]
    realized_trades: list[RealizedTrade]
    stock_market_value: float
    cash_balance: float
    principal: float
    investment_years: float
    account_value: float
    unrealized_pnl: float
    unrealized_pnl_rate: float
    realized_pnl: float
    realized_pnl_rate: float
    account_pnl: float
    account_pnl_rate: float
    annualized_return_rate: float
    today_pnl: float
    dividend_income: float


class PriceStatus(BaseModel):
    total: int
    priced: int
    delayed: int


class DashboardResponse(BaseModel):
    account_value: float
    principal: float
    investment_years: float
    stock_market_value: float
    cash_balance: float
    unrealized_pnl: float
    unrealized_pnl_rate: float
    realized_pnl: float
    realized_pnl_rate: float
    account_pnl: float
    account_pnl_rate: float
    annualized_return_rate: float
    today_pnl: float
    dividend_income: float
    holdings_pie: list[AccountOverviewHolding]
    recent_transactions: list[TransactionRecord]
    price_status: PriceStatus


class PriceQuote(BaseModel):
    code: str
    price: float | None = None
    name: str | None = None
    delayed: bool = False
    source: str = "twse"
