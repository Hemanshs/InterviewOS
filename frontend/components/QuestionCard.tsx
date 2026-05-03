import type { QuestionDetail } from "@/types/interview";

const difficultyStyles: Record<string, string> = {
  easy: "border-emerald-500/40 text-emerald-300",
  medium: "border-amber-500/40 text-amber-300",
  hard: "border-red-500/40 text-red-300",
};

const typeStyles: Record<string, string> = {
  technical: "border-sky-500/40 text-sky-300",
  behavioral: "border-indigo-500/40 text-indigo-300",
};

export function QuestionCard({ question }: { question: QuestionDetail }) {
  const difficultyClass =
    difficultyStyles[question.difficulty] ?? "border-white/20 text-[#d4d4d4]";
  const typeClass =
    typeStyles[question.type] ?? "border-white/20 text-[#d4d4d4]";

  return (
    <section className="rounded-sm border border-white/10 border-l-4 border-l-[#ff6b00] bg-[#1a1a1a] p-6">
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <span className="font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
          Question {question.sequence}
        </span>
        <span
          className={`rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.16em] ${difficultyClass}`}
        >
          {question.difficulty}
        </span>
        <span
          className={`rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.16em] ${typeClass}`}
        >
          {question.type}
        </span>
      </div>

      <h2 className="text-2xl leading-snug text-[#f5f5f5]">
        {question.question_text}
      </h2>

      <div className="mt-5 text-sm uppercase tracking-[0.18em] text-[#8d8d8d]">
        {question.time_limit_seconds} seconds to answer
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {question.expected_focus_areas.map((area) => (
          <span
            key={area}
            className="rounded-full border border-white/15 px-3 py-1 text-xs text-[#cfcfcf]"
          >
            {area}
          </span>
        ))}
      </div>
    </section>
  );
}
