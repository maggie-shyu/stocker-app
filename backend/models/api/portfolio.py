from datetime import date

from pydantic import BaseModel

from backend.models.domain.ledger import TransactionRecord
from backend.models.domain.portfolio import DividendIncomeByStock, DividendRecord, RealizedTrade


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


class RealizedResponse(BaseModel):
    items: list[RealizedTrade]
    dividend_by_stock: list[DividendIncomeByStock]
    all_dividends: list[DividendRecord] = []
    total_realized_pnl: float
    dividend_income: float
    invested_capital: float
    realized_pnl_rate: float
    dividend_realized_pnl_rate: float
    win_rate: float
    avg_win: float
    avg_loss: float


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
