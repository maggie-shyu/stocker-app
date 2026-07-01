CREATE TABLE transactions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid REFERENCES auth.users NOT NULL,
    date            date NOT NULL,
    action          text NOT NULL,
    code            text NOT NULL,
    name            text NOT NULL,
    trade_type      text NOT NULL DEFAULT '一般',
    buy_shares      numeric,
    buy_price       numeric,
    sell_shares     numeric,
    sell_price      numeric,
    dividend_shares numeric,
    dividend_price  numeric,
    reason          text
);
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users see own transactions" ON transactions
    FOR ALL USING (user_id = auth.uid());

CREATE TABLE cashflow (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid REFERENCES auth.users NOT NULL,
    date            date NOT NULL,
    deposit         numeric NOT NULL DEFAULT 0,
    withdrawal      numeric NOT NULL DEFAULT 0
);
ALTER TABLE cashflow ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users see own cashflow" ON cashflow
    FOR ALL USING (user_id = auth.uid());

CREATE TABLE stocks (
    code    text PRIMARY KEY,
    name    text NOT NULL
);

CREATE TABLE user_settings (
    user_id                  uuid PRIMARY KEY REFERENCES auth.users,
    commission_discount_rate numeric NOT NULL DEFAULT 1.0
);
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users see own settings" ON user_settings
    FOR ALL USING (user_id = auth.uid());
