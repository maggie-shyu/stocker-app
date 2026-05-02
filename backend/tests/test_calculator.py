from datetime import date
from pathlib import Path

import pytest

from backend.models.schemas import CashflowRecord, TransactionRecord, UserSettings
from backend.services.calculator import calculate_trade_financials, compute_portfolio
from backend.tests.support.csv_fixture_service import CsvFixtureService


DATA_DIR = Path(__file__).resolve().parent / "data"

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


def test_fifo_portfolio_price_independent_values():
    service = CsvFixtureService(DATA_DIR)
    portfolio = compute_portfolio(
        transactions=service.read_transactions(),
        cashflows=service.read_cashflows(),
        as_of=date(2026, 5, 1),
    )
