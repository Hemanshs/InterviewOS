"use client";

import { useCallback, useRef, useState } from "react";

import { uploadResume } from "@/lib/api";
import type { ResumeUploadResult } from "@/types/interview";

import { ErrorBox } from "./ErrorBox";

interface ResumeUploadCardProps {
  onUploaded: (result: ResumeUploadResult) => void;
  onSkip: () => void;
}

const MAX_FILE_BYTES = 10 * 1024 * 1024;

function getFileError(file: File): string | null {
  const isPdf =
    file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  if (!isPdf) {
    return "Only PDF resumes are supported.";
  }
  if (file.size > MAX_FILE_BYTES) {
    return "Resume must be 10MB or smaller.";
  }
  return null;
}

export function ResumeUploadCard({
  onUploaded,
  onSkip,
}: ResumeUploadCardProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<"idle" | "uploading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      const fileError = getFileError(file);
      if (fileError) {
        setError(fileError);
        setStatus("error");
        return;
      }

      setError(null);
      setStatus("uploading");

      try {
        const response = await uploadResume(file);
        if (!response.success) {
          setDismissed(false);
          setError(response.error.message);
          setStatus("error");
          return;
        }
        if (!response.data.parsed || !response.data.profile) {
          setDismissed(false);
          setError(response.message || "Resume parsing failed.");
          setStatus("error");
          return;
        }
        setDismissed(false);
        onUploaded(response.data);
        setStatus("idle");
      } catch (uploadError) {
        setDismissed(false);
        setError(
          uploadError instanceof Error
            ? uploadError.message
            : "Resume upload failed."
        );
        setStatus("error");
      }
    },
    [onUploaded]
  );

  if (dismissed) {
    return null;
  }

  return (
    <section className="rounded-sm border border-white/10 bg-[#1a1a1a] p-6">
      <div className="mb-4 font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
        Your resume
      </div>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          const file = event.dataTransfer.files?.[0];
          if (file) {
            void handleFile(file);
          }
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-xl border border-dashed px-6 py-10 text-center transition-colors ${
          isDragging
            ? "border-emerald-400/60 bg-emerald-500/5"
            : "border-gray-700 hover:border-gray-500"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              void handleFile(file);
            }
          }}
        />

        <div className="text-4xl">📄</div>
        <div className="mt-4 text-lg text-[#f2f2f2]">
          {status === "uploading"
            ? "Parsing resume with AI..."
            : "Drop your resume here or click to upload"}
        </div>
        <div className="mt-2 text-sm text-[#8f8f8f]">PDF only · Max 10MB</div>
      </div>

      {status === "uploading" ? (
        <div className="mt-4 flex items-center gap-3 text-sm text-[#cfcfcf]">
          <span className="inline-block h-3 w-3 animate-pulse rounded-full bg-emerald-400" />
          Parsing resume with AI...
        </div>
      ) : null}

      {status === "error" && error ? (
        <div className="mt-4 space-y-3">
          <ErrorBox
            message={error}
            onDismiss={() => {
              setError(null);
              setStatus("idle");
            }}
          />
          <button
            onClick={() => {
              setError(null);
              setStatus("idle");
              inputRef.current?.click();
            }}
            className="text-sm text-[#cfcfcf] underline-offset-4 transition-colors hover:text-[#ffffff] hover:underline"
          >
            Try another file
          </button>
        </div>
      ) : null}

      <div className="mt-4 text-center">
        <button
          onClick={() => {
            setDismissed(true);
            onSkip();
          }}
          className="text-sm text-[#7f7f7f] transition-colors hover:text-[#cfcfcf]"
        >
          Skip — start without resume
        </button>
      </div>
    </section>
  );
}
