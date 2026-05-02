ALTER TABLE public.user_settings
ADD COLUMN odd_lot_minimum_fee numeric NOT NULL DEFAULT 1,
ADD COLUMN bond_etf_tax_rate numeric NOT NULL DEFAULT 0;
