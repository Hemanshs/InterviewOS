import type {
  ApiResponse,
  EvaluatePayload,
  EvaluateResult,
  FinalReport,
  FinalReportPayload,
  GenerateQuestionPayload,
  HistoryData,
  QuestionResponseData,
  ResumeUploadResult,
  StartInterviewPayload,
  StartInterviewResult,
  TranscribePayload,
  TranscribeResult,
} from "@/types/interview";

const MOCK_TOKEN = "mock_token_phase_3_1";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const res = await fetch(path, {
    ...options,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${MOCK_TOKEN}`,
      ...options.headers,
    },
  });

  const raw = (await res.json()) as unknown;
  return normalizeApiResponse<T>(raw, res.ok);
}

function normalizeApiResponse<T>(
  raw: unknown,
  resOk: boolean
): ApiResponse<T> {
  if (
    typeof raw === "object" &&
    raw !== null &&
    "success" in raw &&
    (raw as { success: unknown }).success === true
  ) {
    return raw as ApiResponse<T>;
  }

  if (
    typeof raw === "object" &&
    raw !== null &&
    "success" in raw &&
    (raw as { success: unknown }).success === false &&
    "error" in raw &&
    typeof (raw as { error?: unknown }).error === "object" &&
    (raw as { error?: unknown }).error !== null
  ) {
    return raw as ApiResponse<T>;
  }

  const message =
    typeof raw === "object" && raw !== null && "message" in raw
      ? String((raw as { message?: unknown }).message ?? "Request failed")
      : "Request failed";

  const inferredCode =
    message.includes("RATE_LIMIT_EXCEEDED")
      ? "RATE_LIMIT_EXCEEDED"
      : message.includes("SESSION_NOT_FOUND")
        ? "SESSION_NOT_FOUND"
        : resOk
          ? "INTERNAL_ERROR"
          : "REQUEST_FAILED";

  return {
    success: false,
    error: {
      code: inferredCode,
      message,
    },
  };
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await apiFetch<{ status: string }>("/api/health");
    return res.success === true;
  } catch {
    return false;
  }
}

export async function startInterviewSession(
  payload: StartInterviewPayload
): Promise<ApiResponse<StartInterviewResult>> {
  return apiFetch<StartInterviewResult>("/api/interview/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function generateQuestion(
  payload: GenerateQuestionPayload
): Promise<ApiResponse<QuestionResponseData>> {
  return apiFetch<QuestionResponseData>("/api/interview/question", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getInterviewHistory(
  status?: string
): Promise<ApiResponse<HistoryData>> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<HistoryData>(`/api/interview/history${query}`);
}

export async function transcribeAudio(
  payload: TranscribePayload
): Promise<ApiResponse<TranscribeResult>> {
  const formData = new FormData();
  formData.append("session_id", payload.session_id);
  formData.append("question_id", payload.question_id);
  formData.append("duration_seconds", String(payload.duration_seconds));
  formData.append("language", payload.language ?? "en");
  formData.append("audio_file", payload.audio_file, "answer.webm");

  const res = await fetch("/api/audio/transcribe", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${MOCK_TOKEN}`,
    },
    body: formData,
  });

  const data = await res.json();
  return normalizeApiResponse<TranscribeResult>(data, res.ok);
}

export async function evaluateAnswer(
  payload: EvaluatePayload
): Promise<ApiResponse<EvaluateResult>> {
  return apiFetch<EvaluateResult>("/api/interview/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function generateFinalReport(
  payload: FinalReportPayload
): Promise<ApiResponse<FinalReport>> {
  return apiFetch<FinalReport>("/api/interview/final-report", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function uploadResume(
  file: File
): Promise<ApiResponse<ResumeUploadResult>> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/api/resume/upload", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${MOCK_TOKEN}`,
    },
    body: formData,
  });

  const data = await res.json();
  return normalizeApiResponse<ResumeUploadResult>(data, res.ok);
}
