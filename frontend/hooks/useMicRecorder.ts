"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type MicState =
  | "idle"
  | "requesting_permission"
  | "recording"
  | "stopped"
  | "error";

export interface MicRecorderResult {
  blob: Blob;
  durationSeconds: number;
  mimeType: string;
}

export interface UseMicRecorderReturn {
  micState: MicState;
  elapsedSeconds: number;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  reset: () => void;
  result: MicRecorderResult | null;
}

const MAX_DURATION_SECONDS = 60;

function getSupportedMimeType(): string {
  const types = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/aac",
  ];
  for (const type of types) {
    if (MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }
  return "";
}

export function useMicRecorder(): UseMicRecorderReturn {
  const [micState, setMicState] = useState<MicState>("idle");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MicRecorderResult | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const autoStopRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startTimeRef = useRef<number>(0);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (autoStopRef.current) {
        clearTimeout(autoStopRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    if (autoStopRef.current) {
      clearTimeout(autoStopRef.current);
    }
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
  }, []);

  const startRecording = useCallback(async () => {
    setError(null);
    setResult(null);
    setElapsedSeconds(0);
    chunksRef.current = [];

    if (
      typeof window === "undefined" ||
      !navigator.mediaDevices?.getUserMedia
    ) {
      setError(
        "Your browser does not support microphone recording. Please use Chrome or Firefox."
      );
      setMicState("error");
      return;
    }

    if (typeof MediaRecorder === "undefined") {
      setError("MediaRecorder is not supported in this browser.");
      setMicState("error");
      return;
    }

    setMicState("requesting_permission");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = getSupportedMimeType();
      const recorderOptions = mimeType ? { mimeType } : undefined;
      const recorder = recorderOptions
        ? new MediaRecorder(stream, recorderOptions)
        : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const chunkMimeType = chunksRef.current[0]?.type;
        const finalMimeType =
          chunkMimeType || recorder.mimeType || mimeType || "application/octet-stream";
        const blob = new Blob(chunksRef.current, { type: finalMimeType });
        const durationSeconds = Math.round(
          (Date.now() - startTimeRef.current) / 1000
        );
        setResult({ blob, durationSeconds, mimeType: finalMimeType });
        setMicState("stopped");
      };

      recorder.onerror = () => {
        setError("Recording failed. Please try again.");
        setMicState("error");
      };

      recorder.start(250);
      startTimeRef.current = Date.now();
      setMicState("recording");

      timerRef.current = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);

      autoStopRef.current = setTimeout(() => {
        stopRecording();
      }, MAX_DURATION_SECONDS * 1000);
    } catch (err) {
      if (err instanceof DOMException && err.name === "NotAllowedError") {
        setError(
          "Microphone permission denied. Please allow mic access in your browser settings and reload."
        );
      } else if (err instanceof DOMException && err.name === "NotFoundError") {
        setError(
          "No microphone found. Please connect a microphone and try again."
        );
      } else {
        setError(
          "Could not access microphone. Please check your browser settings."
        );
      }
      setMicState("error");
    }
  }, [stopRecording]);

  const reset = useCallback(() => {
    setMicState("idle");
    setElapsedSeconds(0);
    setError(null);
    setResult(null);
    chunksRef.current = [];
  }, []);

  return {
    micState,
    elapsedSeconds,
    error,
    startRecording,
    stopRecording,
    reset,
    result,
  };
}
