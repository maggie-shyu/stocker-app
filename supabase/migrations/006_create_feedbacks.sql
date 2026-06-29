CREATE TABLE IF NOT EXISTS public.feedbacks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subject text NOT NULL CHECK (length(btrim(subject)) > 0),
    body text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS feedbacks_user_id_created_at_idx
    ON public.feedbacks (user_id, created_at DESC);

ALTER TABLE public.feedbacks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users manage own feedbacks" ON public.feedbacks;
CREATE POLICY "users manage own feedbacks" ON public.feedbacks
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE OR REPLACE FUNCTION public.touch_feedbacks_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS touch_feedbacks_updated_at ON public.feedbacks;
CREATE TRIGGER touch_feedbacks_updated_at
    BEFORE UPDATE ON public.feedbacks
    FOR EACH ROW
    EXECUTE FUNCTION public.touch_feedbacks_updated_at();
