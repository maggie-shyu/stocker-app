from datetime import date
from pathlib import Path

import pytest

from services.calculator import calculate_trade_financials, compute_portfolio
from services.csv_service import CsvService


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


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


def test_fifo_portfolio_price_independent_values():
    service = CsvService(DATA_DIR)
    portfolio = compute_portfolio(
        transactions=service.read_transactions(),
        cashflows=service.read_cashflows(),
        as_of=date(2026, 5, 1),
    )

    assert len(portfolio.holdings) == 9
    assert portfolio.principal == pytest.approx(2670399.0)
    assert portfolio.cash_balance == pytest.approx(183507.7999999998)
    assert portfolio.realized_pnl == pytest.approx(961466.2686716791)
    assert portfolio.realized_pnl_rate > 0
    assert portfolio.dividend_income == pytest.approx(7506.0)
    assert portfolio.investment_years > 0
    assert portfolio.annualized_return_rate == pytest.approx(
        (1 + portfolio.account_pnl_rate) ** (1 / portfolio.investment_years) - 1
    )
