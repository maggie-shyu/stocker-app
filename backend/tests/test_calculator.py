from datetime import date
from pathlib import Path

import pytest

from models.schemas import CashflowRecord, TransactionRecord
from services.calculator import calculate_trade_financials, compute_portfolio
from services.csv_service import CsvService


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "tommy"


@pytest.fixture(autouse=True)
def stable_discount_rate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(CsvService, "get_commission_discount_rate", lambda self: 0.0)


def test_fee_preview_matches_minimum_discounted_fee_rule():
    result = calculate_trade_financials(
        action="買",
        trade_type="一般",
        shares=1000,
        price=100,
        current_price=100,
        discount_rate=0,
    )

    assert result.raw_fee == 142.5
    assert result.discounted_fee == 20
    assert result.tax == 0
    assert result.expense == 100020


def test_fee_preview_uses_odd_lot_minimum_fee():
    result = calculate_trade_financials(
        action="買",
        trade_type="一般",
        shares=1,
        price=10,
        current_price=10,
        discount_rate=0,
    )

    assert result.raw_fee == 0.01425
    assert result.discounted_fee == 1
    assert result.tax == 0
    assert result.expense == 11


def test_sell_tax_uses_standard_stock_rate():
    result = calculate_trade_financials(
        action="賣",
        code="2330",
        trade_type="一般",
        shares=1000,
        price=100,
        current_price=100,
        discount_rate=0,
    )

    assert result.tax == pytest.approx(300)


def test_sell_tax_uses_day_trade_rate_for_stocks():
    result = calculate_trade_financials(
        action="賣",
        code="2330",
        trade_type="當沖",
        shares=1000,
        price=100,
        current_price=100,
        discount_rate=0,
    )

    assert result.tax == pytest.approx(150)


def test_sell_tax_uses_etf_rate():
    result = calculate_trade_financials(
        action="賣",
        code="0050",
        trade_type="一般",
        shares=1000,
        price=100,
        current_price=100,
        discount_rate=0,
    )

    assert result.tax == pytest.approx(100)


def test_fifo_portfolio_price_independent_values():
    service = CsvService(DATA_DIR)
    portfolio = compute_portfolio(
        transactions=service.read_transactions(),
        cashflows=service.read_cashflows(),
        as_of=date(2026, 5, 1),
    )

    assert len(portfolio.holdings) > 0
    assert portfolio.principal == pytest.approx(2670399.0)
    assert portfolio.cash_balance == pytest.approx(183564.8)
    assert portfolio.realized_pnl > 0
    assert portfolio.realized_pnl_rate > 0
    assert portfolio.dividend_income > 0
    assert portfolio.realized_pnl >= portfolio.dividend_income
    assert portfolio.investment_years > 0
    assert portfolio.annualized_return_rate == pytest.approx(
        (1 + portfolio.account_pnl_rate) ** (1 / portfolio.investment_years) - 1
    )


def test_realized_trade_uses_weighted_stock_prices_without_fees():
    portfolio = compute_portfolio(
        transactions=[
            TransactionRecord(
                id="1",
                date=date(2026, 1, 1),
                action="買",
                code="2330",
                name="台積電",
                buy_shares=100,
                buy_price=100,
                expense=10020,
            ),
            TransactionRecord(
                id="2",
                date=date(2026, 1, 2),
                action="買",
                code="2330",
                name="台積電",
                buy_shares=100,
                buy_price=120,
                expense=12020,
            ),
            TransactionRecord(
                id="3",
                date=date(2026, 1, 3),
                action="賣",
                code="2330",
                name="台積電",
                sell_shares=150,
                sell_price=130,
                income=19422,
            ),
        ],
        cashflows=[CashflowRecord(id="c1", date=date(2026, 1, 1), deposit=50000, withdrawal=0)],
        as_of=date(2026, 1, 3),
    )

    assert len(portfolio.realized_trades) == 1
    trade = portfolio.realized_trades[0]
    assert trade.avg_buy_price == pytest.approx(106.666666666667)
    assert trade.avg_sell_price == pytest.approx(130)
