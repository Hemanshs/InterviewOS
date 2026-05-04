"use client";

import { createClient } from "@supabase/supabase-js";
import type { Session, User } from "@supabase/supabase-js";
import { createContext, createElement, useContext, useEffect, useState } from "react";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

type SupabaseSessionContextValue = {
  session: Session | null;
  user: User | null;
  loading: boolean;
  configured: boolean;
};

const SupabaseSessionContext = createContext<SupabaseSessionContextValue>({
  session: null,
  user: null,
  loading: true,
  configured: isSupabaseConfigured,
});

export function SupabaseSessionProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    let active = true;
    supabase.auth.getSession().then(({ data }) => {
      if (!active) {
        return;
      }
      setSession(data.session ?? null);
      setUser(data.session?.user ?? null);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession ?? null);
      setUser(nextSession?.user ?? null);
      setLoading(false);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  return createElement(
    SupabaseSessionContext.Provider,
    {
      value: {
        session,
        user,
        loading,
        configured: isSupabaseConfigured,
      },
    },
    children
  );
}

export function useSupabaseSession() {
  return useContext(SupabaseSessionContext);
}

export async function getAccessToken(): Promise<string | null> {
  if (!supabase) {
    return null;
  }
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export async function getCurrentUser() {
  if (!supabase) {
    return null;
  }
  const { data } = await supabase.auth.getUser();
  return data.user ?? null;
}
