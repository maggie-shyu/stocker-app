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
  previous_close: number;
  market_value: number;
  cost_basis: number;
  cumulative_dividend: number;
  cumulative_pnl: number;
  cumulative_pnl_rate: number;
  unrealized_pnl: number;
  unrealized_pnl_rate: number;
  weight: number;
};
