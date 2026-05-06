from datetime import date

from pydantic import BaseModel

from backend.models.domain.ledger import TradeType


class StockLookup(BaseModel):
    code: str
    name: str


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
    net_avg_cost: float
    avg_cost: float
    current_price: float
    market_value: float
    cost_basis: float
    cumulative_dividend: float
    cumulative_pnl: float
    cumulative_pnl_rate: float
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


class PriceQuote(BaseModel):
    code: str
    price: float | None = None
    previous_close: float | None = None
    name: str | None = None
    delayed: bool = False
    source: str = "twse"
