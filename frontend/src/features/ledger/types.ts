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

export type TransactionPage = {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
};

export type Cashflow = {
  id: string;
  date: string;
  deposit: number;
  withdrawal: number;
};
