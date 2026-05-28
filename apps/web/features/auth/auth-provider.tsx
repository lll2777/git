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
  getAccessToken: () => Promise<string | null>;
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

  const getAccessToken = useCallback(async () => {
    if (!supabase) {
      setSession(null);
      return null;
    }

    const { data, error } = await supabase.auth.getSession();
    if (error || !data.session) {
      setSession(null);
      return null;
    }

    const expiresAt = data.session.expires_at ?? 0;
    const shouldRefresh = expiresAt * 1000 - Date.now() < 60_000;
    const session = shouldRefresh
      ? await refreshStoredSession(supabase)
      : data.session;

    if (!session) {
      await clearInvalidSession(supabase);
      setSession(null);
      return null;
    }

    const { error: userError } = await supabase.auth.getUser(
      session.access_token,
    );
    if (userError) {
      const refreshedSession = await refreshStoredSession(supabase);
      if (refreshedSession) {
        const { error: refreshedUserError } = await supabase.auth.getUser(
          refreshedSession.access_token,
        );
        if (!refreshedUserError) {
          setSession(refreshedSession);
          return refreshedSession.access_token;
        }
      }

      await clearInvalidSession(supabase);
      setSession(null);
      return null;
    }

    setSession(session);
    return session.access_token;
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
      getAccessToken,
      refreshSession,
      signOut,
    }),
    [getAccessToken, isLoading, refreshSession, session, signOut, supabase],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

async function refreshStoredSession(
  supabase: NonNullable<ReturnType<typeof getSupabaseBrowserClient>>,
) {
  const { data, error } = await supabase.auth.refreshSession();
  if (error || !data.session) {
    return null;
  }
  return data.session;
}

async function clearInvalidSession(
  supabase: NonNullable<ReturnType<typeof getSupabaseBrowserClient>>,
) {
  try {
    await supabase.auth.signOut({ scope: "local" });
  } catch {
    await supabase.auth.signOut().catch(() => undefined);
  }
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}
