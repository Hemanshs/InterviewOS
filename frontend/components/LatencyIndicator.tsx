import type { LatencyStateType } from "@/types/interview";

const STATE_LABELS: Record<string, string> = {
  idle: "",
  question_generating: "Preparing your question...",
  voice_generating: "Generating interviewer voice...",
  ready_for_answer: "Your turn to answer",
  recording_answer: "Recording your answer...",
  uploading_audio: "Uploading your answer...",
  transcribing_answer: "Transcribing your answer...",
  transcript_ready: "Answer received",
  evaluating_answer: "Evaluating your response...",
  preparing_follow_up: "Preparing follow-up question...",
  evaluation_ready: "Evaluation complete",
  next_question_loading: "Loading next question...",
  interview_complete: "Interview complete",
  final_report_generating: "Generating your scorecard...",
  scorecard_ready: "Scorecard ready",
  error: "Something went wrong",
};

const DOT_STYLES: Record<Exclude<LatencyStateType, "idle">, string> = {
  question_generating: "bg-[#ff6b00] animate-pulse",
  voice_generating: "bg-[#ff6b00] animate-pulse",
  recording_answer: "bg-red-500 animate-pulse",
  uploading_audio: "bg-[#ff6b00] animate-pulse",
  transcribing_answer: "bg-[#ff6b00] animate-pulse",
  evaluating_answer: "bg-[#ff6b00] animate-pulse",
  preparing_follow_up: "bg-[#ff6b00] animate-pulse",
  next_question_loading: "bg-[#ff6b00] animate-pulse",
  final_report_generating: "bg-[#ff6b00] animate-pulse",
  ready_for_answer: "bg-emerald-400",
  transcript_ready: "bg-emerald-400",
  evaluation_ready: "bg-emerald-400",
  interview_complete: "bg-emerald-400",
  scorecard_ready: "bg-emerald-400",
  error: "bg-red-500",
};

export function LatencyIndicator({ state }: { state: LatencyStateType }) {
  if (state === "idle") {
    return null;
  }

  const isLoading =
    state === "question_generating" ||
    state === "voice_generating" ||
    state === "uploading_audio" ||
    state === "transcribing_answer" ||
    state === "evaluating_answer" ||
    state === "preparing_follow_up" ||
    state === "next_question_loading" ||
    state === "final_report_generating";

  return (
    <div className="flex items-center justify-center gap-3 rounded-sm border border-white/10 bg-[#111111] px-4 py-3 font-mono text-sm text-[#d4d4d4]">
      <span
        className={`h-2.5 w-2.5 rounded-full ${DOT_STYLES[state]}`}
        aria-hidden="true"
      />
      <span>{STATE_LABELS[state]}</span>
      {isLoading ? (
        <span className="inline-block h-4 w-px animate-pulse bg-[#ff6b00]" />
      ) : null}
    </div>
  );
}
