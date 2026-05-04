"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getAccessToken, supabase, useSupabaseSession } from "@/lib/supabaseClient";

export function UserMenu({ email }: { email: string }) {
  const [open, setOpen] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { configured } = useSupabaseSession();
  const router = useRouter();

  const displayEmail = useMemo(() => {
    if (email.length <= 28) {
      return email;
    }
    return `${email.slice(0, 12)}...${email.slice(-12)}`;
  }, [email]);

  const handleSignOut = async () => {
    if (configured && supabase) {
      await supabase.auth.signOut();
    }
    router.push("/login");
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE_MY_ACCOUNT") {
      return;
    }

    setSubmitting(true);
    try {
      const token = await getAccessToken();
      await fetch("/api/account", {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token ?? "mock_token"}`,
        },
        body: JSON.stringify({ confirmation: "DELETE_MY_ACCOUNT" }),
      });
    } finally {
      if (configured && supabase) {
        await supabase.auth.signOut();
      }
      router.push("/login");
      setSubmitting(false);
    }
  };

  return (
    <>
      <div className="relative">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="rounded-full border border-white/10 bg-[#111111] px-3 py-2 text-xs font-mono text-[#cfcfcf] transition-colors hover:border-white/20 hover:bg-[#161616]"
        >
          {displayEmail}
        </button>

        {open ? (
          <div className="absolute right-0 mt-2 w-72 rounded-xl border border-white/10 bg-[#111111] p-3 shadow-2xl">
            <div className="border-b border-white/10 pb-3">
              <div className="text-[11px] font-mono uppercase tracking-[0.18em] text-[#7e7e7e]">
                Signed in
              </div>
              <div className="mt-2 text-sm text-[#f5f5f5] break-all">{email}</div>
            </div>
            <div className="mt-3 space-y-2">
              <button
                type="button"
                onClick={handleSignOut}
                className="w-full rounded-lg border border-white/10 px-3 py-2 text-left text-sm text-[#f5f5f5] transition-colors hover:bg-[#191919]"
              >
                Sign out
              </button>
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="w-full rounded-lg border border-[#5f1f1f] px-3 py-2 text-left text-sm text-[#ff9e9e] transition-colors hover:bg-[#261111]"
              >
                Delete account
              </button>
            </div>
          </div>
        ) : null}
      </div>

      {showDeleteConfirm ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#111111] p-6 shadow-2xl">
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-[#f5f5f5]">Delete account</h3>
              <p className="text-sm text-[#9a9a9a]">
                Type <span className="font-mono text-[#f5f5f5]">DELETE_MY_ACCOUNT</span> to confirm.
              </p>
              <input
                value={deleteConfirmText}
                onChange={(event) => setDeleteConfirmText(event.target.value)}
                className="w-full rounded-lg border border-white/10 bg-[#0d0d0d] px-3 py-3 text-sm text-[#f5f5f5] outline-none focus:border-[#ff6b00]/50"
                placeholder="DELETE_MY_ACCOUNT"
              />
            </div>
            <div className="mt-5 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeleteConfirmText("");
                }}
                className="rounded-lg border border-white/10 px-4 py-2 text-sm text-[#cfcfcf] transition-colors hover:bg-[#191919]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={submitting || deleteConfirmText !== "DELETE_MY_ACCOUNT"}
                className="rounded-lg border border-[#ff6b00] bg-[#ff6b00] px-4 py-2 text-sm font-semibold text-[#111111] transition-colors hover:bg-[#ff7d26] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {submitting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
