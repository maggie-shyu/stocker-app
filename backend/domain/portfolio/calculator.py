from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date

from backend.models.api.portfolio import RealizedResponse
from backend.models.domain.ledger import TradeFinancials, TransactionRecord, UserSettings
from backend.models.domain.portfolio import (
    DividendIncomeByStock,
    DividendRecord,
    Holding,
    HoldingLot,
    PortfolioSnapshot,
    RealizedTrade,
)


def _money(value: float) -> float:
    return round(float(value), 12)


@dataclass
class Lot:
    date: date
    shares: float
    cost_per_share: float
    price_per_share: float
    trade_type: str = "一般"

    @property
    def cost_basis(self) -> float:
        return self.shares * self.cost_per_share


def _to_float(value: float | None) -> float:
    return float(value or 0)


def _is_taiwan_etf_code(code: str | None) -> bool:
    normalized = (code or "").strip()
    return normalized.startswith("00")


def _is_bond_etf_code(code: str | None) -> bool:
    normalized = (code or "").strip()
    return normalized.startswith("00") and normalized.upper().endswith("B")


def _is_odd_lot(shares: float | None) -> bool:
    if shares is None:
        return False
    remainder = abs(float(shares)) % 1000
    return remainder > 1e-9 and abs(remainder - 1000) > 1e-9


def _resolve_trade_shares(tx: TransactionRecord) -> float:
    return _to_float(tx.buy_shares if tx.action == "買" else tx.sell_shares)


def _build_visible_lots(raw_lots: deque[Lot]) -> list[HoldingLot]:
    return [
        HoldingLot(
            date=lot.date,
            shares=_money(lot.shares),
            cost_per_share=_money(lot.cost_per_share),
            cost_basis=_money(lot.cost_basis),
            trade_type=lot.trade_type,
        )
        for lot in raw_lots
        if lot.shares > 1e-9
    ]


def _sell_lots(lots: deque[Lot], shares_to_sell: float, day_trade_date: date | None = None) -> tuple[float, float]:
    consumed_cost = 0.0
    consumed_buy_amount = 0.0
    remaining = shares_to_sell

    # For 當沖 sells: consume same-day 當沖 lots before regular FIFO lots,
    # so the 當沖 buy is matched to its own sell rather than eating older normal lots.
    if day_trade_date is not None:
        for lot in lots:
            if remaining <= 1e-9:
                break
            if lot.trade_type == "當沖" and lot.date == day_trade_date:
                taken = min(remaining, lot.shares)
                consumed_cost += taken * lot.cost_per_share
                consumed_buy_amount += taken * lot.price_per_share
                lot.shares -= taken
                remaining -= taken
        # Prune any lots fully consumed by the 當沖 pass
        non_empty = [lot for lot in lots if lot.shares > 1e-9]
        lots.clear()
        lots.extend(non_empty)

    # Regular FIFO for remaining shares
    while remaining > 1e-9 and lots:
        lot = lots[0]
        taken = min(remaining, lot.shares)
        consumed_cost += taken * lot.cost_per_share
        consumed_buy_amount += taken * lot.price_per_share
        lot.shares -= taken
        remaining -= taken
        if lot.shares <= 1e-9:
            lots.popleft()

    return consumed_cost, consumed_buy_amount


def calculate_trade_financials(
    *,
    action: str,
    trade_type: str,
    code: str | None = None,
    shares: float | None = None,
    price: float | None = None,
    amount: float | None = None,
    current_price: float = 0,
    settings: UserSettings | None = None,
) -> TradeFinancials:
    if amount is None:
        amount = float(shares or 0) * float(price or 0)
    else:
        amount = float(amount)

    if not settings:
        settings = UserSettings(commission_discount_rate=1.0)

    if action == "股利":
        transfer_fee = settings.cash_dividend_transfer_fee if shares is not None and price is not None and amount > 0 else 0
        return TradeFinancials(
            current_price=current_price,
            amount=_money(amount),
            discounted_fee=_money(transfer_fee),
            trade_cost=_money(transfer_fee),
            income=_money(amount - transfer_fee),
            discount_rate=settings.commission_discount_rate,
        )

    raw_fee = amount * settings.base_commission_rate
    min_fee = settings.odd_lot_minimum_fee if _is_odd_lot(shares) else settings.minimum_fee
    discounted_fee = max(raw_fee * settings.commission_discount_rate, min_fee) if amount > 0 else 0
    if action == "賣":
        if _is_bond_etf_code(code):
            tax_rate = settings.bond_etf_tax_rate
        elif _is_taiwan_etf_code(code):
            tax_rate = settings.etf_tax_rate
        else:
            tax_rate = settings.day_trade_tax_rate if trade_type == "當沖" else settings.stock_tax_rate
        tax = amount * tax_rate
        income = amount - discounted_fee - tax
        expense = 0
    else:
        tax = 0
        expense = amount + discounted_fee
        income = 0

    return TradeFinancials(
        current_price=current_price,
        raw_fee=_money(raw_fee),
        discounted_fee=_money(discounted_fee),
        tax=_money(tax),
        amount=_money(amount),
        trade_cost=_money(discounted_fee + tax),
        expense=_money(expense),
        income=_money(income),
        discount_rate=settings.commission_discount_rate,
    )


def compute_portfolio(
    *,
    transactions: list[TransactionRecord],
    cashflows: list,
    live_prices: dict[str, float] | None = None,
    previous_closes: dict[str, float] | None = None,
    as_of: date | None = None,
) -> PortfolioSnapshot:
    lots_by_code: dict[str, deque[Lot]] = defaultdict(deque)
    names: dict[str, str] = {}
    current_prices: dict[str, float] = {}
    realized_trades: list[RealizedTrade] = []
    dividend_income = 0.0
    today_pnl = 0.0
    yesterday_stock_value = 0.0
    # per-stock cumulative totals for 累積損益
    sell_income_by_code: dict[str, float] = defaultdict(float)
    sell_trade_cost_by_code: dict[str, float] = defaultdict(float)  # sell_fee + sell_tax
    dividend_by_code: dict[str, float] = defaultdict(float)

    # Buys must be processed before sells on the same date so 當沖 buy lots exist when sell runs
    _ACTION_ORDER = {"買": 0, "賣": 1, "股利": 2}
    for tx in sorted(transactions, key=lambda item: (item.date, _ACTION_ORDER.get(item.action, 99), item.id)):
        names[tx.code] = tx.name
        if tx.current_price:
            current_prices[tx.code] = tx.current_price

        if tx.action == "買":
            shares = _resolve_trade_shares(tx)
            if shares <= 0:
                continue
            lots_by_code[tx.code].append(
                Lot(
                    date=tx.date,
                    shares=shares,
                    cost_per_share=_to_float(tx.expense) / shares,
                    price_per_share=_to_float(tx.buy_price),
                    trade_type=tx.trade_type,
                )
            )
        elif tx.action == "賣":
            shares_to_sell = _resolve_trade_shares(tx)
            sell_income_by_code[tx.code] += _to_float(tx.income)
            sell_trade_cost_by_code[tx.code] += _to_float(tx.trade_cost)
            day_trade_date = tx.date if tx.trade_type == "當沖" else None
            consumed_cost, consumed_buy_amount = _sell_lots(lots_by_code[tx.code], shares_to_sell, day_trade_date)
            pnl = _to_float(tx.income) - consumed_cost
            realized_trades.append(
                RealizedTrade(
                    date=tx.date,
                    code=tx.code,
                    name=tx.name,
                    shares=shares_to_sell,
                    avg_buy_price=_money(consumed_buy_amount / shares_to_sell) if shares_to_sell else 0,
                    avg_sell_price=_money(_to_float(tx.sell_price)),
                    income=_to_float(tx.income),
                    cost_basis=_money(consumed_cost),
                    realized_pnl=_money(pnl),
                    realized_pnl_rate=(pnl / consumed_cost) if consumed_cost else 0,
                    trade_type=tx.trade_type,
                    reason=tx.reason,
                )
            )
        elif tx.action == "股利":
            inc = _to_float(tx.income)
            dividend_income += inc
            dividend_by_code[tx.code] += inc

    if live_prices:
        current_prices.update(live_prices)

    stock_market_value = sum(
        sum(lot.shares for lot in lots) * current_prices.get(code, 0)
        for code, lots in lots_by_code.items()
    )

    holdings: list[Holding] = []
    for code, lots in lots_by_code.items():
        visible_lots = _build_visible_lots(lots)
        if not visible_lots:
            continue
        total_shares = sum(lot.shares for lot in visible_lots)
        cost_basis = sum(lot.cost_basis for lot in visible_lots)
        current_price = current_prices.get(code, 0)
        previous_close = (previous_closes or {}).get(code, current_price)
        if total_shares > 0:
            today_pnl += (current_price - previous_close) * total_shares
            yesterday_stock_value += previous_close * total_shares

        market_value = total_shares * current_price
        unrealized = market_value - cost_basis

        total_sell_inc = sell_income_by_code[code]
        stock_div = dividend_by_code[code]
        remaining_buy_amount = sum(lot.shares * lot.price_per_share for lot in lots)
        # 買均: 剩餘庫存批次的原始買入均價（FIFO 扣除已賣出股數後）
        avg_cost = remaining_buy_amount / total_shares if total_shares else 0
        # 成本均: (買入總金額+手續費−累計股利收入) / 持股總股數
        net_avg_cost = (cost_basis - stock_div) / total_shares if total_shares else 0
        net_invested = cost_basis
        # 持股累積損益 = 市值 - 賣出手續費 - 交易稅 + 累計股息 - (買進金額 + 買進手續費)
        cum_pnl = market_value + stock_div - cost_basis - sell_trade_cost_by_code[code]
        cum_pnl_rate = cum_pnl / net_invested if net_invested else 0

        holdings.append(
            Holding(
                code=code,
                name=names.get(code, code),
                lots=visible_lots,
                total_shares=_money(total_shares),
                net_avg_cost=_money(net_avg_cost),
                avg_cost=_money(avg_cost),
                current_price=_money(current_price),
                previous_close=_money(previous_close),
                market_value=_money(market_value),
                cost_basis=_money(cost_basis),
                cumulative_dividend=_money(stock_div),
                cumulative_pnl=_money(cum_pnl),
                cumulative_pnl_rate=cum_pnl_rate,
                unrealized_pnl=_money(unrealized),
                unrealized_pnl_rate=(unrealized / cost_basis) if cost_basis else 0,
                weight=(market_value / stock_market_value) if stock_market_value else 0,
            )
        )

    holdings.sort(key=lambda item: item.market_value, reverse=True)
    
    today = date.today()
    realized_dividend_income = 0.0
    for tx in transactions:
        if tx.action == "股利" and tx.date <= today:
            realized_dividend_income += _to_float(tx.income)

    trade_realized_pnl = sum(item.realized_pnl for item in realized_trades)
    realized_pnl = trade_realized_pnl + realized_dividend_income
    realized_invested_capital = sum(item.cost_basis for item in realized_trades)
    cost_basis_open = sum(item.cost_basis for item in holdings)
    unrealized_pnl = stock_market_value - cost_basis_open
    deposits = sum(_to_float(item.deposit) for item in cashflows)
    withdrawals = sum(_to_float(item.withdrawal) for item in cashflows)
    principal = deposits - withdrawals
    cash_balance = (
        principal
        - sum(_to_float(tx.expense) for tx in transactions)
        + sum(_to_float(tx.income) for tx in transactions)
    )
    account_value = stock_market_value + cash_balance
    account_pnl = account_value - principal
    as_of_date = as_of or date.today()
    candidate_dates = [tx.date for tx in transactions] + [item.date for item in cashflows]
    start_date = min(candidate_dates) if candidate_dates else as_of_date
    elapsed_days = max((as_of_date - start_date).days, 0)
    investment_years = max(elapsed_days / 365, 1 / 365) if candidate_dates else 0
    total_return_base = 1 + (account_pnl / principal) if principal else 0
    annualized_return_rate = (
        (total_return_base ** (1 / investment_years)) - 1
        if investment_years > 0 and total_return_base > 0
        else 0
    )

    return PortfolioSnapshot(
        holdings=holdings,
        realized_trades=realized_trades,
        stock_market_value=_money(stock_market_value),
        cash_balance=_money(cash_balance),
        principal=_money(principal),
        investment_years=_money(investment_years),
        account_value=_money(account_value),
        unrealized_pnl=_money(unrealized_pnl),
        unrealized_pnl_rate=(unrealized_pnl / cost_basis_open) if cost_basis_open else 0,
        realized_pnl=_money(realized_pnl),
        realized_pnl_rate=(realized_pnl / realized_invested_capital) if realized_invested_capital else 0,
        account_pnl=_money(account_pnl),
        account_pnl_rate=(account_pnl / principal) if principal else 0,
        annualized_return_rate=annualized_return_rate,
        today_pnl=_money(today_pnl),
        today_pnl_rate=(today_pnl / yesterday_stock_value) if yesterday_stock_value else 0,
        dividend_income=_money(dividend_income),
    )


def summarize_realized(
    items: list[RealizedTrade],
    dividend_income: float = 0,
    dividend_by_stock: list[DividendIncomeByStock] | None = None,
    all_dividends: list[DividendRecord] | None = None,
) -> RealizedResponse:
    wins = [item.realized_pnl for item in items if item.realized_pnl > 0]
    losses = [item.realized_pnl for item in items if item.realized_pnl < 0]
    invested_capital = sum(item.cost_basis for item in items)
    total_realized_pnl = sum(item.realized_pnl for item in items) + dividend_income
    return RealizedResponse(
        items=items,
        dividend_by_stock=dividend_by_stock or [],
        all_dividends=all_dividends or [],
        total_realized_pnl=_money(total_realized_pnl),
        dividend_income=_money(dividend_income),
        invested_capital=_money(invested_capital),
        realized_pnl_rate=(total_realized_pnl / invested_capital) if invested_capital else 0,
        dividend_realized_pnl_rate=(dividend_income / total_realized_pnl) if total_realized_pnl else 0,
        win_rate=(len(wins) / len(items)) if items else 0,
        avg_win=_money(sum(wins) / len(wins)) if wins else 0,
        avg_loss=_money(sum(losses) / len(losses)) if losses else 0,
    )
