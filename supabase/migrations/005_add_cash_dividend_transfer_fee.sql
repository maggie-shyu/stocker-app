ALTER TABLE public.user_settings
ADD COLUMN IF NOT EXISTS cash_dividend_transfer_fee numeric NOT NULL DEFAULT 10;

ALTER TABLE public.transactions
ADD COLUMN IF NOT EXISTS dividend_shares numeric,
ADD COLUMN IF NOT EXISTS dividend_price numeric;
