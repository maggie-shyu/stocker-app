import type { Session } from "@supabase/supabase-js";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { isSupabaseConfigured, supabaseConfigError } from "../../platform/auth/supabase";
import {
  getCurrentSession,
  signInWithPassword,
  signOutSession,
  signUpWithPassword,
  subscribeToSessionChanges,
  updateSessionPassword,
} from "../../platform/auth/session";

type AuthContextValue = {
  session: Session | null;
  loading: boolean;
  configError: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  updatePassword: (currentPassword: string, newPassword: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(isSupabaseConfigured);

  useEffect(() => {
    if (!isSupabaseConfigured) {
      setLoading(false);
      return;
    }

    getCurrentSession().then((currentSession) => {
      setSession(currentSession);
      setLoading(false);
    });

    return subscribeToSessionChanges((nextSession: Session | null) => {
      setSession(nextSession);
      setLoading(false);
    });
  }, []);

  const signIn = async (email: string, password: string) => {
    await signInWithPassword(email, password);
  };

  const signUp = async (email: string, password: string) => {
    await signUpWithPassword(email, password);
  };

  const signOut = async () => {
    await signOutSession();
  };

  const updatePassword = async (currentPassword: string, newPassword: string) => {
    await updateSessionPassword(currentPassword, newPassword);
  };

  return (
    <AuthContext.Provider value={{ session, loading, configError: supabaseConfigError, signIn, signUp, signOut, updatePassword }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
