export type UserSettings = {
  commission_discount_rate: number;
  base_commission_rate: number;
  minimum_fee: number;
  odd_lot_minimum_fee: number;
  cash_dividend_transfer_fee: number;
  stock_tax_rate: number;
  day_trade_tax_rate: number;
  etf_tax_rate: number;
  bond_etf_tax_rate: number;
};

export type Feedback = {
  id: string;
  subject: string;
  body: string;
  created_at?: string | null;
  updated_at?: string | null;
};
