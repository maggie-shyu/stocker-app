from datetime import date
from pathlib import Path

import pytest

from backend.domain.portfolio.calculator import calculate_trade_financials, compute_portfolio
from backend.models.domain.ledger import CashflowRecord, TransactionRecord, UserSettings
from backend.tests.support.fixture_ledger_store import FixtureLedgerStore


DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Helper: settings with zero discount (fee = minimum only)
_NO_DISCOUNT = UserSettings(commission_discount_rate=0)


def test_fee_preview_matches_minimum_discounted_fee_rule():
    result = calculate_trade_financials(
        action="買",
        trade_type="一般",
        shares=1000,
        price=100,
        current_price=100,
        settings=_NO_DISCOUNT,
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
        settings=_NO_DISCOUNT,
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
        settings=_NO_DISCOUNT,
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
        settings=_NO_DISCOUNT,
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
        settings=_NO_DISCOUNT,
    )

    assert result.tax == pytest.approx(100)


def test_sell_tax_uses_bond_etf_rate_for_b_suffix():
    """Bond ETFs (00-prefix + B-suffix) use bond_etf_tax_rate, not etf_tax_rate."""
    settings = UserSettings(commission_discount_rate=0, bond_etf_tax_rate=0.0)
    result = calculate_trade_financials(
        action="賣",
        code="00720B",
        trade_type="一般",
        shares=1000,
        price=100,
        current_price=100,
        settings=settings,
    )

    assert result.tax == pytest.approx(0)


def test_sell_tax_non_b_suffix_etf_not_treated_as_bond():
    """00-prefix without B-suffix uses etf_tax_rate."""
    result = calculate_trade_financials(
        action="賣",
        code="0056",
        trade_type="一般",
        shares=1000,
        price=100,
        current_price=100,
        settings=_NO_DISCOUNT,
    )

    assert result.tax == pytest.approx(100)


def test_odd_lot_minimum_fee_from_settings():
    """Odd-lot minimum fee comes from settings.odd_lot_minimum_fee, not hardcoded 1."""
    settings = UserSettings(commission_discount_rate=0, odd_lot_minimum_fee=5)
    result = calculate_trade_financials(
        action="買",
        trade_type="一般",
        shares=500,  # odd lot
        price=1,
        current_price=1,
        settings=settings,
    )

    assert result.discounted_fee == 5


def test_cash_dividend_income_subtracts_transfer_fee():
    result = calculate_trade_financials(
        action="股利",
        trade_type="一般",
        shares=1000,
        price=1.5,
        settings=UserSettings(cash_dividend_transfer_fee=10),
    )

    assert result.amount == pytest.approx(1500)
    assert result.discounted_fee == pytest.approx(10)
    assert result.trade_cost == pytest.approx(10)
    assert result.income == pytest.approx(1490)


def test_fifo_portfolio_price_independent_values():
    service = FixtureLedgerStore(DATA_DIR)
    portfolio = compute_portfolio(
        transactions=service.read_transactions(),
        cashflows=service.read_cashflows(),
        as_of=date(2026, 5, 1),
    )


def test_holdings_averages_use_only_remaining_fifo_lots():
    portfolio = compute_portfolio(
        transactions=[
            TransactionRecord(
                id="buy-1",
                date=date(2025, 1, 1),
                action="買",
                code="2330",
                name="台積電",
                buy_shares=1000,
                buy_price=10,
                expense=10010,
                amount=10000,
            ),
            TransactionRecord(
                id="buy-2",
                date=date(2025, 1, 2),
                action="買",
                code="2330",
                name="台積電",
                buy_shares=1000,
                buy_price=20,
                expense=20020,
                amount=20000,
            ),
            TransactionRecord(
                id="sell-1",
                date=date(2025, 1, 3),
                action="賣",
                code="2330",
                name="台積電",
                sell_shares=1500,
                sell_price=30,
                income=44900,
                amount=45000,
                trade_cost=100,
            ),
        ],
        cashflows=[],
        live_prices={"2330": 25},
        as_of=date(2025, 1, 3),
    )

    holding = portfolio.holdings[0]

    assert holding.total_shares == pytest.approx(500)
    assert holding.avg_cost == pytest.approx(20)
    assert holding.net_avg_cost == pytest.approx(20.02)
