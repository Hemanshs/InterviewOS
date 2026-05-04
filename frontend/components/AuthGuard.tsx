"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useSupabaseSession } from "@/lib/supabaseClient";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { loading, session, configured } = useSupabaseSession();
  const router = useRouter();

  useEffect(() => {
    if (loading || !configured) {
      return;
    }
    if (!session) {
      router.push("/login");
    }
  }, [configured, loading, router, session]);

  if (loading) {
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
