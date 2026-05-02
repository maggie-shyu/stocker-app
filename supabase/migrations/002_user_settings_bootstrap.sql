CREATE TABLE IF NOT EXISTS public.user_settings (
    user_id uuid PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
    commission_discount_rate numeric NOT NULL DEFAULT 1.0
);

ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'user_settings'
          AND policyname = 'users see own settings'
    ) THEN
        CREATE POLICY "users see own settings" ON public.user_settings
            FOR ALL
            USING ((SELECT auth.uid()) = user_id)
            WITH CHECK ((SELECT auth.uid()) = user_id);
    END IF;
END
$$;

CREATE OR REPLACE FUNCTION public.initialize_user_settings()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.user_settings (user_id, commission_discount_rate)
    VALUES (NEW.id, 1.0)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created_initialize_settings ON auth.users;

CREATE TRIGGER on_auth_user_created_initialize_settings
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.initialize_user_settings();

INSERT INTO public.user_settings (user_id, commission_discount_rate)
SELECT id, 1.0
FROM auth.users
ON CONFLICT (user_id) DO NOTHING;
