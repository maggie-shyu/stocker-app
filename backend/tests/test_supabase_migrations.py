from pathlib import Path


def test_user_settings_bootstrap_migration_contains_table_policy_trigger_and_backfill():
    migration = (
        Path(__file__).resolve().parents[2]
        / "supabase"
        / "migrations"
        / "002_user_settings_bootstrap.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS public.user_settings" in migration
    assert 'CREATE POLICY "users see own settings" ON public.user_settings' in migration
    assert "CREATE OR REPLACE FUNCTION public.initialize_user_settings()" in migration
    assert "CREATE TRIGGER on_auth_user_created_initialize_settings" in migration
    assert "INSERT INTO public.user_settings (user_id, commission_discount_rate)" in migration


def test_cashflow_migrations_remove_obsolete_principal_fields():
    init_migration = (
        Path(__file__).resolve().parents[2]
        / "supabase"
        / "migrations"
        / "001_init.sql"
    ).read_text(encoding="utf-8")
    cleanup_migration = (
        Path(__file__).resolve().parents[2]
        / "supabase"
        / "migrations"
        / "003_drop_cashflow_is_principal.sql"
    ).read_text(encoding="utf-8")

    assert "is_principal" not in init_migration
    assert "DROP COLUMN IF EXISTS is_principal" in cleanup_migration
