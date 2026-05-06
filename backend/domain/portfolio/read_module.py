from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.domain.ledger.interfaces import LedgerStore, StockCatalog
from backend.domain.portfolio.calculator import compute_portfolio, summarize_realized
from backend.domain.portfolio.price_service import PriceService
from backend.models.api.portfolio import AccountOverviewHolding, DashboardResponse, PriceStatus, RealizedResponse
from backend.models.domain.ledger import TransactionRecord
from backend.models.domain.portfolio import DividendIncomeByStock, Holding, PortfolioSnapshot, PriceQuote


@dataclass
class PortfolioReadResult:
    transactions: list[TransactionRecord]
    portfolio: PortfolioSnapshot
    price_status: PriceStatus
    benchmark_return_rate: float | None
    start_date: date | None


def _unique_codes(transactions: list[TransactionRecord]) -> list[str]:
    return list({tx.code for tx in transactions})


def _build_price_maps(codes: list[str], quotes: list[PriceQuote]) -> tuple[dict[str, float], dict[str, float], PriceStatus]:
    live = {
        quote.code: quote.price
        for quote in quotes
        if getattr(quote, "price", None) is not None
    }
    previous_closes = {
        quote.code: quote.previous_close
        for quote in quotes
        if getattr(quote, "previous_close", None) is not None
    }
    return live, previous_closes, PriceStatus(
        total=len(codes),
        priced=len(live),
        delayed=max(len(codes) - len(live), 0),
    )


async def read_portfolio(
    ledger_store: LedgerStore,
    stock_catalog: StockCatalog,
    prices: PriceService,
) -> PortfolioReadResult:
    transactions = ledger_store.read_transactions()
    cashflows = ledger_store.read_cashflows()
    codes = _unique_codes(transactions)
    quotes = await prices.get_prices(codes, stock_catalog.read_stocks())
    live_prices, previous_closes, price_status = _build_price_maps(codes, quotes)
    portfolio = compute_portfolio(
        transactions=transactions,
        cashflows=cashflows,
        live_prices=live_prices,
        previous_closes=previous_closes,
    )

    start_date = min((tx.date for tx in transactions), default=None)
    benchmark_return_rate = None
    if start_date is not None:
        benchmark_return_rate = await prices.get_benchmark_return_rate("0050.TW", start_date)

    return PortfolioReadResult(
        transactions=transactions,
        portfolio=portfolio,
        price_status=price_status,
        benchmark_return_rate=benchmark_return_rate,
        start_date=start_date,
    )


async def read_dashboard(
    ledger_store: LedgerStore,
    stock_catalog: StockCatalog,
    prices: PriceService,
) -> DashboardResponse:
    result = await read_portfolio(ledger_store, stock_catalog, prices)
    portfolio = result.portfolio
    holdings_pie = [
        AccountOverviewHolding(
            code=holding.code,
            name=holding.name,
            market_value=holding.market_value,
            weight=holding.weight,
        )
        for holding in portfolio.holdings
    ]

    return DashboardResponse(
        account_value=portfolio.account_value,
        principal=portfolio.principal,
        investment_years=portfolio.investment_years,
        stock_market_value=portfolio.stock_market_value,
        cash_balance=portfolio.cash_balance,
        unrealized_pnl=portfolio.unrealized_pnl,
        unrealized_pnl_rate=portfolio.unrealized_pnl_rate,
        realized_pnl=portfolio.realized_pnl,
        realized_pnl_rate=portfolio.realized_pnl_rate,
        account_pnl=portfolio.account_pnl,
        account_pnl_rate=portfolio.account_pnl_rate,
        annualized_return_rate=portfolio.annualized_return_rate,
        today_pnl=portfolio.today_pnl,
        today_pnl_rate=portfolio.today_pnl_rate,
        dividend_income=portfolio.dividend_income,
        benchmark_return_rate=result.benchmark_return_rate,
        start_date=result.start_date,
        holdings_pie=holdings_pie,
        recent_transactions=result.transactions[-3:][::-1],
        price_status=result.price_status,
    )


async def read_holdings(
    ledger_store: LedgerStore,
    stock_catalog: StockCatalog,
    prices: PriceService,
) -> list[Holding]:
    return (await read_portfolio(ledger_store, stock_catalog, prices)).portfolio.holdings


def read_realized(
    ledger_store: LedgerStore,
    *,
    code: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> RealizedResponse:
    transactions = ledger_store.read_transactions()
    portfolio = compute_portfolio(
        transactions=transactions,
        cashflows=ledger_store.read_cashflows(),
    )
    items = portfolio.realized_trades
    if code:
        items = [item for item in items if item.code == code]
    if from_date:
        items = [item for item in items if item.date >= from_date]
    if to_date:
        items = [item for item in items if item.date <= to_date]

    dividend_by_stock_map: dict[str, DividendIncomeByStock] = {}
    today = date.today()
    dividend_income = 0.0
    for tx in transactions:
        if tx.action != "股利":
            continue
        if tx.date > today:
            continue
        if code and tx.code != code:
            continue
        if from_date and tx.date < from_date:
            continue
        if to_date and tx.date > to_date:
            continue
        dividend = float(tx.income or 0)
        dividend_income += dividend
        current = dividend_by_stock_map.get(tx.code)
        if current:
            current.dividend_income += dividend
            continue
        dividend_by_stock_map[tx.code] = DividendIncomeByStock(
            code=tx.code,
            name=tx.name,
            dividend_income=dividend,
        )

    dividend_by_stock = sorted(
        dividend_by_stock_map.values(),
        key=lambda item: item.dividend_income,
        reverse=True,
    )
    return summarize_realized(
        items,
        dividend_income=dividend_income,
        dividend_by_stock=dividend_by_stock,
    )
