from pathlib import Path


def test_user_settings_bootstrap_migration_contains_table_policy_trigger_and_backfill():
    migration = (
        Path(__file__).resolve().parents[4]
        / "supabase"
        / "migrations"
        / "002_user_settings_bootstrap.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS public.user_settings" in migration
    assert 'CREATE POLICY "users see own settings" ON public.user_settings' in migration
    assert "CREATE OR REPLACE FUNCTION public.initialize_user_settings()" in migration
    assert "CREATE TRIGGER on_auth_user_created_initialize_settings" in migration
    assert "INSERT INTO public.user_settings (user_id, commission_discount_rate)" in migration


def test_cash_dividend_migration_contains_settings_columns():
    migration = (
        Path(__file__).resolve().parents[4]
        / "supabase"
        / "migrations"
        / "005_add_cash_dividend_transfer_fee.sql"
    ).read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS cash_dividend_transfer_fee numeric NOT NULL DEFAULT 10" in migration
    assert "ADD COLUMN IF NOT EXISTS dividend_shares numeric" in migration
    assert "ADD COLUMN IF NOT EXISTS dividend_price numeric" in migration


def test_feedbacks_migration_contains_table_policies_and_timestamp_trigger():
    migration = (
        Path(__file__).resolve().parents[4]
        / "supabase"
        / "migrations"
        / "006_create_feedbacks.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS public.feedbacks" in migration
    assert "user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE" in migration
    assert "subject text NOT NULL CHECK (length(btrim(subject)) > 0)" in migration
    assert "body text NOT NULL DEFAULT ''" in migration
    assert "ALTER TABLE public.feedbacks ENABLE ROW LEVEL SECURITY" in migration
    assert 'CREATE POLICY "users manage own feedbacks" ON public.feedbacks' in migration
    assert "CREATE TRIGGER touch_feedbacks_updated_at" in migration


def test_feedback_subject_migration_renames_content_and_adds_subject():
    migration = (
        Path(__file__).resolve().parents[4]
        / "supabase"
        / "migrations"
        / "007_add_feedback_subject.sql"
    ).read_text(encoding="utf-8")

    assert "ALTER TABLE public.feedbacks RENAME COLUMN content TO body" in migration
    assert "ADD COLUMN IF NOT EXISTS subject text NOT NULL DEFAULT ''" in migration
    assert "ADD COLUMN IF NOT EXISTS body text NOT NULL DEFAULT ''" in migration
