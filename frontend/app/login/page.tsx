"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { getAccessToken, supabase, useSupabaseSession } from "@/lib/supabaseClient";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const { configured } = useSupabaseSession();
  const router = useRouter();
  const searchParams = useSearchParams();

  const verifyActiveAccount = async (): Promise<boolean> => {
    const token = await getAccessToken();
    const response = await fetch("/api/me", {
      headers: {
        Authorization: `Bearer ${token ?? ""}`,
      },
    });
    const payload = await response.json();
    if (response.ok && payload?.success) {
      return true;
    }
    if (payload?.error?.code === "ACCOUNT_DELETED") {
      await supabase?.auth.signOut();
      setError("This account was deleted and cannot be used again.");
      return false;
    }
    setError(payload?.error?.message || "Unable to verify your account.");
    return false;
  };

  const handleSubmit = async () => {
    if (!supabase) {
      router.push("/interview");
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      if (mode === "login") {
        const { error: authError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (authError) {
          setError(authError.message);
        } else {
          const active = await verifyActiveAccount();
          if (active) {
            router.push("/interview");
          }
        }
      } else {
        const { error: authError } = await supabase.auth.signUp({
          email,
          password,
        });
        if (authError) {
          setError(authError.message);
        } else {
          setMessage("Check your email to confirm your account.");
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0a0a0a] px-6 py-12">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#111111] p-8 shadow-2xl">
        <div className="space-y-3 text-center">
          <div className="font-mono text-xs uppercase tracking-[0.28em] text-[#8d8d8d]">
            Phase 4.5 auth
          </div>
          <h1 className="text-4xl tracking-tight text-[#f5f5f5]">InterviewOS</h1>
          <p className="text-sm text-[#9a9a9a]">
            {configured
              ? "Sign in to continue your interview practice"
              : "Supabase is not configured. Local dev bypass is active."}
          </p>
        </div>

        <div className="mt-8 flex rounded-full border border-white/10 bg-[#0d0d0d] p-1">
          {(["login", "signup"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => {
                setMode(value);
                setError(null);
                setMessage(null);
              }}
              className={`flex-1 rounded-full px-4 py-2 text-sm transition-colors ${
                mode === value
                  ? "bg-[#ff6b00] text-[#111111]"
                  : "text-[#9a9a9a]"
              }`}
            >
              {value === "login" ? "Login" : "Sign Up"}
            </button>
          ))}
        </div>

        <div className="mt-6 space-y-4">
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="Email"
            className="w-full rounded-lg border border-white/10 bg-[#0d0d0d] px-4 py-3 text-sm text-[#f5f5f5] outline-none transition-colors placeholder:text-[#6f6f6f] focus:border-[#ff6b00]/50"
          />
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            className="w-full rounded-lg border border-white/10 bg-[#0d0d0d] px-4 py-3 text-sm text-[#f5f5f5] outline-none transition-colors placeholder:text-[#6f6f6f] focus:border-[#ff6b00]/50"
          />
          {error ? (
            <div className="rounded-lg border border-[#5f1f1f] bg-[#231111] px-4 py-3 text-sm text-[#ffb4b4]">
              {error}
            </div>
          ) : searchParams.get("error") === "account_deleted" ? (
            <div className="rounded-lg border border-[#5f1f1f] bg-[#231111] px-4 py-3 text-sm text-[#ffb4b4]">
              This account was deleted and can no longer be used.
            </div>
          ) : null}
          {message ? (
            <div className="rounded-lg border border-[#25401f] bg-[#152012] px-4 py-3 text-sm text-[#b2e3a0]">
              {message}
            </div>
          ) : null}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading || !email || !password}
            className="w-full rounded-lg border border-[#ff6b00] bg-[#ff6b00] px-4 py-3 font-semibold text-[#111111] transition-colors hover:bg-[#ff7d26] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? mode === "login"
                ? "Signing in..."
                : "Creating account..."
              : mode === "login"
                ? "Sign in"
                : "Create account"}
          </button>
          {!configured ? (
            <button
              type="button"
              onClick={() => router.push("/interview")}
              className="w-full rounded-lg border border-white/10 px-4 py-3 text-sm text-[#cfcfcf] transition-colors hover:bg-[#191919]"
            >
              Continue in dev mode
            </button>
          ) : null}
        </div>
      </div>
    </main>
  );
}
