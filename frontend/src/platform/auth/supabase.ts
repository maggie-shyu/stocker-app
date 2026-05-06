import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabasePublishableKey =
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ??
  import.meta.env.VITE_SUPABASE_ANON_KEY;

function isPlaceholder(value: string | undefined) {
  if (!value) return true;
  return (
    value.includes("your-project-id") ||
    value.includes("your-anon-public-key") ||
    value.includes("your-publishable-key")
  );
}

export const supabaseConfigError =
  isPlaceholder(supabaseUrl) || isPlaceholder(supabasePublishableKey)
    ? "Supabase is not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in frontend/.env and restart the frontend dev server."
    : null;

export const isSupabaseConfigured = supabaseConfigError === null;

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabasePublishableKey)
  : null;
