"use client";

import { useEffect, useMemo, useState } from "react";

import { transcribeAudio } from "@/lib/api";
import { useMicRecorder } from "@/hooks/useMicRecorder";
import type { LatencyStateType, TranscribeResult } from "@/types/interview";

interface MicRecorderProps {
  questionId: string;
  sessionId: string;
  onTranscriptReady: (result: TranscribeResult) => void;
  onError: (message: string) => void;
  disabled?: boolean;
  onStateChange?: (state: LatencyStateType) => void;
}

type UploadState =
  | "idle"
  | "uploading"
  | "transcribing"
  | "error";

function formatElapsed(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainder = String(seconds % 60).padStart(2, "0");
  return `${minutes}:${remainder}`;
}

export function MicRecorder({
  questionId,
  sessionId,
  onTranscriptReady,
  onError,
  disabled = false,
  onStateChange,
}: MicRecorderProps) {
  const {
    micState,
    elapsedSeconds,
    error,
    startRecording,
    stopRecording,
    reset,
    result,
  } = useMicRecorder();
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [uploadError, setUploadError] = useState<string | null>(null);

  const isBusy =
    micState === "requesting_permission" ||
    micState === "recording" ||
    uploadState === "uploading" ||
    uploadState === "transcribing";

  useEffect(() => {
    if (micState === "recording") {
      onStateChange?.("recording_answer");
    } else if (uploadState === "uploading") {
      onStateChange?.("uploading_audio");
    } else if (uploadState === "transcribing") {
      onStateChange?.("transcribing_answer");
    } else if (
      uploadState === "idle" &&
      micState === "idle" &&
      !result
    ) {
      onStateChange?.("ready_for_answer");
    }
  }, [micState, onStateChange, result, uploadState]);

  useEffect(() => {
    if (!result) {
      return;
    }

    const currentResult = result;
    let cancelled = false;

    async function runTranscription() {
      setUploadError(null);
      setUploadState("uploading");
      onStateChange?.("uploading_audio");

      const responsePromise = transcribeAudio({
        session_id: sessionId,
        question_id: questionId,
        duration_seconds: currentResult.durationSeconds,
        audio_file: new File(
          [currentResult.blob],
          currentResult.mimeType.includes("mp4")
            ? "answer.m4a"
            : currentResult.mimeType.includes("aac")
              ? "answer.aac"
              : "answer.webm",
          { type: currentResult.mimeType || currentResult.blob.type }
        ),
      });

      setUploadState("transcribing");
      onStateChange?.("transcribing_answer");

      const response = await responsePromise;

      if (cancelled) {
        return;
      }

      if (!response.success) {
        setUploadState("error");
        setUploadError(response.error.message);
        onError(response.error.message);
        return;
      }

      setUploadState("idle");
      onTranscriptReady(response.data);
      reset();
    }

    runTranscription().catch((err) => {
      if (cancelled) {
        return;
      }
      setUploadState("error");
      setUploadError(
        err instanceof Error
          ? err.message
          : "Transcription failed. Please try again."
      );
      onError(
        err instanceof Error
          ? err.message
          : "Transcription failed. Please try again."
      );
    });

    return () => {
      cancelled = true;
    };
  }, [onError, onStateChange, onTranscriptReady, questionId, reset, result, sessionId]);

  const currentError = uploadError ?? error;
  const tenSecondsRemaining = elapsedSeconds >= 50 && micState === "recording";
  const statusLabel = useMemo(() => {
    if (micState === "requesting_permission") {
      return "Requesting microphone...";
    }
    if (uploadState === "uploading") {
      return "Uploading...";
    }
    if (uploadState === "transcribing") {
      return "Transcribing...";
    }
    return null;
  }, [micState, uploadState]);

  return (
    <section className="rounded-sm border border-white/10 bg-[#1a1a1a] px-5 py-5">
      <div className="mb-4 font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
        Your answer
      </div>

      {statusLabel ? (
        <div className="flex items-center gap-3 text-sm text-[#c9c9c9]">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ff6b00] animate-pulse" />
          <span>{statusLabel}</span>
        </div>
      ) : null}

      {micState === "idle" && uploadState === "idle" ? (
        <button
          onClick={() => {
            setUploadError(null);
            onStateChange?.("recording_answer");
            void startRecording();
          }}
          disabled={disabled}
          className="rounded-sm border border-[#ff6b00] bg-[#ff6b00] px-6 py-3 font-semibold text-[#111111] transition-colors hover:bg-[#ff7d26] disabled:cursor-not-allowed disabled:opacity-50"
        >
          🎙 Start Answer
        </button>
      ) : null}

      {micState === "recording" ? (
        <div className="space-y-4">
          <div className="flex items-center gap-3 font-mono text-lg text-[#f5f5f5]">
            <span className="h-3 w-3 rounded-full bg-red-500 animate-pulse" />
            <span>{formatElapsed(elapsedSeconds)}</span>
          </div>
          {tenSecondsRemaining ? (
            <p className="text-sm text-amber-300">10 seconds remaining</p>
          ) : null}
          <button
            onClick={stopRecording}
            className="rounded-sm border border-red-500/50 px-6 py-3 font-semibold text-red-300 transition-colors hover:bg-red-500/10"
          >
            Stop Recording
          </button>
        </div>
      ) : null}

      {(uploadState === "uploading" || uploadState === "transcribing") ? (
        <button
          disabled
          className="rounded-sm border border-white/10 px-6 py-3 font-semibold text-[#8d8d8d] opacity-80"
        >
          {uploadState === "uploading" ? "Uploading..." : "Transcribing..."}
        </button>
      ) : null}

      {(micState === "error" || uploadState === "error") && currentError ? (
        <div className="space-y-4">
          <p className="text-sm text-red-300">{currentError}</p>
          <button
            onClick={() => {
              reset();
              setUploadState("idle");
              setUploadError(null);
            }}
            className="rounded-sm border border-red-500/40 px-5 py-2 text-sm text-red-200 transition-colors hover:bg-red-500/10"
          >
            Try Again
          </button>
        </div>
      ) : null}
    </section>
  );
}
