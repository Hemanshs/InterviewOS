"use client";

import { useMemo, useState } from "react";

import type { CompletedAnswer } from "@/types/interview";

interface AnswerReviewProps {
  answers: CompletedAnswer[];
}

function truncate(text: string, max: number) {
  return text.length > max ? `${text.slice(0, max).trimEnd()}...` : text;
}

function getScoreStyle(score: number | null) {
  if (score === null) {
    return "border-white/15 text-[#d4d4d4]";
  }
  if (score >= 7) {
    return "border-emerald-500/30 text-emerald-300";
  }
  if (score >= 5) {
    return "border-amber-500/30 text-amber-300";
  }
  return "border-red-500/30 text-red-300";
}

export function AnswerReview({ answers }: AnswerReviewProps) {
  const [expanded, setExpanded] = useState(false);
  const orderedAnswers = useMemo(() => [...answers].reverse(), [answers]);

  return (
    <section className="rounded-sm border border-white/10 bg-[#121212] px-5 py-5">
      <div className="flex items-center justify-between gap-4">
        <div className="font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
          Answers so far
        </div>
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="rounded-sm border border-white/10 px-3 py-1 text-xs text-[#d3d3d3] transition-colors hover:bg-white/5"
        >
          {expanded ? "Hide" : "Show"}
        </button>
      </div>

      {!expanded ? null : answers.length === 0 ? (
        <p className="mt-4 text-sm text-[#8f8f8f]">No answers yet</p>
      ) : (
        <div className="mt-4 space-y-3">
          {orderedAnswers.map((answer) => (
            <article
              key={answer.answerId}
              className="space-y-2 rounded-sm border border-white/10 bg-[#181818] px-4 py-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs uppercase tracking-[0.16em] text-[#f0f0f0]">
                  Q{answer.questionNumber}
                </span>
                <span className="rounded-full border border-sky-500/25 px-2.5 py-0.5 text-[11px] uppercase tracking-[0.14em] text-sky-300">
                  {answer.questionType}
                </span>
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-[11px] font-mono ${getScoreStyle(answer.overallScore)}`}
                >
                  {answer.overallScore !== null
                    ? `${answer.overallScore.toFixed(1)} / 10`
                    : "-- / 10"}
                </span>
              </div>
              <p className="text-sm text-[#dfdfdf]">
                {truncate(answer.questionText, 80)}
              </p>
              <p className="text-sm text-[#9b9b9b]">
                {truncate(answer.feedbackSummary, 100)}
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
