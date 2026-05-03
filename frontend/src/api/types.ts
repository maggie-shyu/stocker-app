export type Transaction = {
  id: string;
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
  raw_fee?: number;
  discounted_fee?: number;
  tax?: number;
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
  today_pnl_rate: number;
  dividend_income: number;
  benchmark_return_rate?: number;
  start_date?: string;
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
  trade_type: "一般" | "當沖";
};

export type Holding = {
  code: string;
  name: string;
  lots: HoldingLot[];
  total_shares: number;
  net_avg_cost: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  cumulative_dividend: number;
  cumulative_pnl: number;
  cumulative_pnl_rate: number;
  unrealized_pnl: number;
  unrealized_pnl_rate: number;
  weight: number;
};

export type RealizedTrade = {
  date: string;
  code: string;
  name: string;
  shares: number;
  avg_buy_price: number;
  avg_sell_price: number;
  income: number;
  cost_basis: number;
  realized_pnl: number;
  realized_pnl_rate: number;
  trade_type: "一般" | "當沖";
  reason?: string | null;
};

export type DividendIncomeByStock = {
  code: string;
  name: string;
  dividend_income: number;
};

export type RealizedResponse = {
  items: RealizedTrade[];
  dividend_by_stock: DividendIncomeByStock[];
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
  id: string;
  date: string;
  deposit: number;
  withdrawal: number;
};

export type UserSettings = {
  commission_discount_rate: number;
  base_commission_rate: number;
  minimum_fee: number;
  odd_lot_minimum_fee: number;
  stock_tax_rate: number;
  day_trade_tax_rate: number;
  etf_tax_rate: number;
  bond_etf_tax_rate: number;
};

export type AdminCapabilities = {
  is_admin: boolean;
};

export type AdminOverview = {
  total_users: number;
  users_with_transactions: number;
  users_with_cashflows: number;
  supabase_memory_usage_percent: number | null;
  cpu_busy_percent: number | null;
  disk_usage_percent: number | null;
  connection_rate_percent: number | null;
  active_queries: number | null;
};

export type AdminTableSummary = {
  name: string;
  label: string;
  description: string;
  row_count: number;
};

export type AdminTablePage = {
  table_name: string;
  label: string;
  page: number;
  page_size: number;
  total: number;
  columns: string[];
  items: Array<Record<string, string | number | boolean | null>>;
};
