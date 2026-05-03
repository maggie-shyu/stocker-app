from datetime import date
from typing import Any, Literal

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
    id: str
    date: date
    deposit: float = 0
    withdrawal: float = 0


class CashflowCreate(BaseModel):
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


class AuthenticatedUser(BaseModel):
    id: str
    email: str | None = None


class CurrentUserCapabilities(BaseModel):
    is_admin: bool


class AdminOverview(BaseModel):
    total_users: int
    users_with_transactions: int
    users_with_cashflows: int
    supabase_memory_usage_percent: float | None = None
    cpu_busy_percent: float | None = None
    disk_usage_percent: float | None = None
    connection_rate_percent: float | None = None
    active_queries: int | None = None


class AdminTableSummary(BaseModel):
    name: str
    label: str
    description: str
    row_count: int


class AdminTablePage(BaseModel):
    table_name: str
    label: str
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total: int = Field(ge=0)
    columns: list[str]
    items: list[dict[str, Any]]


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
    trade_type: TradeType = "一般"


class Holding(BaseModel):
    code: str
    name: str
    lots: list[HoldingLot]
    total_shares: float
    net_avg_cost: float        # (累計買入 - 累計賣出 - 累計股息) / 剩餘股數
    avg_cost: float            # 累計買入總金額 / 累計買入股數
    current_price: float
    market_value: float
    cost_basis: float
    cumulative_dividend: float # 此股累計股息收入
    cumulative_pnl: float      # (市值 + 累計股息) - 持股總成本
    cumulative_pnl_rate: float # cumulative_pnl / 持股總成本
    unrealized_pnl: float
    unrealized_pnl_rate: float
    weight: float


class RealizedTrade(BaseModel):
    date: date
    code: str
    name: str
    shares: float
    avg_buy_price: float = 0
    avg_sell_price: float = 0
    income: float
    cost_basis: float
    realized_pnl: float
    realized_pnl_rate: float
    trade_type: TradeType = "一般"
    reason: str | None = None


class DividendIncomeByStock(BaseModel):
    code: str
    name: str
    dividend_income: float


class RealizedResponse(BaseModel):
    items: list[RealizedTrade]
    dividend_by_stock: list[DividendIncomeByStock]
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
    today_pnl_rate: float
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
    today_pnl_rate: float
    dividend_income: float
    benchmark_return_rate: float | None = None
    start_date: date | None = None
    holdings_pie: list[AccountOverviewHolding]
    recent_transactions: list[TransactionRecord]
    price_status: PriceStatus


class PriceQuote(BaseModel):
    code: str
    price: float | None = None
    previous_close: float | None = None
    name: str | None = None
    delayed: bool = False
    source: str = "twse"
