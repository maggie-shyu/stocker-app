ALTER TABLE public.user_settings
ADD COLUMN base_commission_rate numeric NOT NULL DEFAULT 0.001425,
ADD COLUMN minimum_fee numeric NOT NULL DEFAULT 20,
ADD COLUMN stock_tax_rate numeric NOT NULL DEFAULT 0.003,
ADD COLUMN day_trade_tax_rate numeric NOT NULL DEFAULT 0.0015,
ADD COLUMN etf_tax_rate numeric NOT NULL DEFAULT 0.001;
