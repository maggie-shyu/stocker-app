export type Transaction = {
  id: number;
  date: string;
  action: "買" | "賣" | "股利";
  code: string;
  name: string;
  trade_type: "一般" | "當沖";
  buy_shares?: number | null;
  buy_price?: number | null;
  sell_shares?: number | null;
  sell_price?: number | null;
  current_price: number;
  amount: number;
  expense: number;
  income: number;
  reason?: string | null;
};

export type HoldingPieItem = {
  code?: string | null;
  name: string;
  market_value: number;
  weight: number;
};

export type Dashboard = {
  account_value: number;
  principal: number;
  investment_years: number;
  stock_market_value: number;
  cash_balance: number;
  unrealized_pnl: number;
  unrealized_pnl_rate: number;
  realized_pnl: number;
  realized_pnl_rate: number;
  account_pnl: number;
  account_pnl_rate: number;
  annualized_return_rate: number;
  today_pnl: number;
  dividend_income: number;
  holdings_pie: HoldingPieItem[];
  recent_transactions: Transaction[];
  price_status: {
    total: number;
    priced: number;
    delayed: number;
  };
};

export type TransactionPage = {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
};

export type HoldingLot = {
  date: string;
  shares: number;
  cost_per_share: number;
  cost_basis: number;
};

export type Holding = {
  code: string;
  name: string;
  lots: HoldingLot[];
  total_shares: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  unrealized_pnl_rate: number;
  weight: number;
};

export type RealizedTrade = {
  date: string;
  code: string;
  name: string;
  shares: number;
  income: number;
  cost_basis: number;
  realized_pnl: number;
  realized_pnl_rate: number;
};

export type RealizedResponse = {
  items: RealizedTrade[];
  total_realized_pnl: number;
  dividend_income: number;
  invested_capital: number;
  realized_pnl_rate: number;
  dividend_realized_pnl_rate: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
};

export type Cashflow = {
  id: number;
  date: string;
  deposit: number;
  withdrawal: number;
  principal_snapshot?: number | null;
};

export type CommissionSettings = {
  commission_discount_rate: number;
};
