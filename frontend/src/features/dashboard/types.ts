import type { Transaction } from "../ledger/types";

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
