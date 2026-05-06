"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getAccessToken, supabase, useSupabaseSession } from "@/lib/supabaseClient";

const verifiedAccountTokens = new Set<string>();

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { loading, session, configured } = useSupabaseSession();
  const [checkingAccount, setCheckingAccount] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    if (loading || !configured) {
      setCheckingAccount(true);
      return;
    }
    if (!session) {
      setCheckingAccount(false);
      router.push("/login");
      return;
    }

    const verifyAccount = async () => {
      try {
        const token = await getAccessToken();
        if (!token) {
          return;
        }
        if (verifiedAccountTokens.has(token)) {
          return;
        }
        const response = await fetch("/api/me", {
          headers: {
            Authorization: `Bearer ${token ?? ""}`,
          },
        });
        const payload = await response.json();
        if (response.ok && payload?.success) {
          verifiedAccountTokens.add(token);
          return;
        }
        if (!response.ok && payload?.error?.code === "ACCOUNT_DELETED") {
          verifiedAccountTokens.delete(token);
          await supabase?.auth.signOut();
          if (!cancelled) {
            router.push("/login?error=account_deleted");
          }
          return;
        }
      } catch {
        // Let existing route/API behavior handle transient backend issues.
      } finally {
        if (!cancelled) {
          setCheckingAccount(false);
        }
      }
    };

    void verifyAccount();

    return () => {
      cancelled = true;
    };
  }, [configured, loading, router, session]);

  if (loading || checkingAccount) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <p className="text-gray-500 font-mono text-sm">Loading...</p>
      </div>
    );
  }

  if (!configured) {
    return <>{children}</>;
  }

  if (!session) {
    return null;
  }

  return <>{children}</>;
}
