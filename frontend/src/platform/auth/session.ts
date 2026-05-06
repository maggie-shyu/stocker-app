import type { Session } from "@supabase/supabase-js";

import { supabase, supabaseConfigError } from "./supabase";

function requireSupabase() {
  if (!supabase) {
    throw new Error(supabaseConfigError ?? "Supabase is not configured.");
  }
  return supabase;
}

export async function getCurrentSession() {
  if (!supabase) {
    return null;
  }

  const { data } = await supabase.auth.getSession();
  return data.session;
}

export function subscribeToSessionChanges(onChange: (session: Session | null) => void) {
  if (!supabase) {
    return () => undefined;
  }

  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange((_event, nextSession) => {
    onChange(nextSession);
  });

  return () => subscription.unsubscribe();
}

export async function signInWithPassword(email: string, password: string) {
  const { error } = await requireSupabase().auth.signInWithPassword({ email, password });
  if (error) {
    throw error;
  }
}

export async function signUpWithPassword(email: string, password: string) {
  const { error } = await requireSupabase().auth.signUp({ email, password });
  if (error) {
    throw error;
  }
}

export async function signOutSession() {
  const { error } = await requireSupabase().auth.signOut();
  if (error) {
    throw error;
  }
}

export async function updateSessionPassword(currentPassword: string, newPassword: string) {
  const { error } = await requireSupabase().auth.updateUser({
    password: newPassword,
    current_password: currentPassword,
  });
  if (error) {
    throw error;
  }
}
