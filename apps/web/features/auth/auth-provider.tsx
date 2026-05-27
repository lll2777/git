"use client";

import type { Session, User } from "@supabase/supabase-js";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getSupabaseBrowserClient } from "@/lib/supabase/client";

type AuthContextValue = {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  isConfigured: boolean;
  refreshSession: () => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const supabase = getSupabaseBrowserClient();
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(supabase));

  const refreshSession = useCallback(async () => {
    if (!supabase) {
      setSession(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    const { data } = await supabase.auth.getSession();
    setSession(data.session);
    setIsLoading(false);
  }, [supabase]);

  const signOut = useCallback(async () => {
    if (!supabase) {
      return;
    }
    await supabase.auth.signOut();
    setSession(null);
  }, [supabase]);

  useEffect(() => {
    if (!supabase) {
      return;
    }

    const client = supabase;
    let isMounted = true;

    async function loadInitialSession() {
      const { data } = await client.auth.getSession();
      if (!isMounted) {
        return;
      }
      setSession(data.session);
      setIsLoading(false);
    }

    void loadInitialSession();

    const {
      data: { subscription },
    } = client.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setIsLoading(false);
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, [supabase]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: session?.user ?? null,
      session,
      isLoading,
      isConfigured: Boolean(supabase),
      refreshSession,
      signOut,
    }),
    [isLoading, refreshSession, session, signOut, supabase],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}
