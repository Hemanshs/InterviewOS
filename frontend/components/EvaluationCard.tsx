"use client";

import { useMemo, useState } from "react";

import type { EvaluateResult } from "@/types/interview";

interface EvaluationCardProps {
  result: EvaluateResult;
  onEvaluateAgain?: () => void;
}

const SCORE_LABELS: Record<string, string> = {
  technical_correctness: "Technical",
  clarity: "Clarity",
  depth: "Depth",
  confidence: "Confidence",
  relevance: "Relevance",
  structure: "Structure",
  communication: "Communication",
  conciseness: "Conciseness",
  example_quality: "Examples",
};

function getScoreStyles(score: number | null) {
  if (score === null) {
    return "bg-[#141414] text-[#b5b5b5] border border-white/10";
  }
  if (score >= 8) {
    return "bg-[#1a2e1a] text-emerald-300 border border-emerald-500/25";
  }
  if (score >= 6) {
    return "bg-[#2a2000] text-amber-300 border border-amber-500/25";
  }
  return "bg-[#2a0f0f] text-red-300 border border-red-500/25";
}

function getOverallColor(score: number | null) {
  if (score === null) {
    return "text-[#d5d5d5]";
  }
  if (score >= 7) {
    return "text-emerald-300";
  }
  if (score >= 5) {
    return "text-amber-300";
  }
  return "text-red-300";
}

export function EvaluationCard({
  result,
  onEvaluateAgain,
}: EvaluationCardProps) {
  const [showIdealPoints, setShowIdealPoints] = useState(false);

  const scoreEntries = useMemo(
    () =>
      Object.entries(result.scores).filter(
        ([key]) => key !== "overall"
      ) as Array<[keyof typeof result.scores, number | null]>,
    [result.scores]
  );

  const overallDisplay =
    result.scores.overall !== null ? result.scores.overall.toFixed(1) : "--";
  const latencySeconds = (result.latency.evaluation_ms / 1000).toFixed(1);

  return (
    <section className="rounded-sm border border-white/10 bg-[#1a1a1a] p-6">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div className="font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
          Evaluation
        </div>
        <div className={`text-right font-mono text-3xl ${getOverallColor(result.scores.overall)}`}>
          <div>{overallDisplay} / 10</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        {scoreEntries.map(([key, value]) => (
          <div
            key={key}
            className={`rounded-sm px-4 py-3 ${getScoreStyles(value)}`}
          >
            <div className="text-xs uppercase tracking-[0.14em] opacity-80">
              {SCORE_LABELS[key]}
            </div>
            <div className="mt-1 font-mono text-lg">
              {value !== null ? value : "--"}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 space-y-6">
        <div>
          <h3 className="mb-2 font-mono text-xs uppercase tracking-[0.18em] text-[#8d8d8d]">
            Summary
          </h3>
          <p className="text-base leading-7 text-[#ededed]">
            {result.feedback.summary}
          </p>
        </div>

        <div>
          <h3 className="mb-2 font-mono text-xs uppercase tracking-[0.18em] text-emerald-300">
            Strengths
          </h3>
          <ul className="space-y-2 text-sm text-[#d9d9d9]">
            {result.feedback.strengths.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-emerald-300">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="mb-2 font-mono text-xs uppercase tracking-[0.18em] text-amber-300">
            Improvements
          </h3>
          <ul className="space-y-2 text-sm text-[#d9d9d9]">
            {result.feedback.improvements.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-amber-300">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <button
            onClick={() => setShowIdealPoints((prev) => !prev)}
            className="font-mono text-xs uppercase tracking-[0.18em] text-[#9e9e9e] transition-colors hover:text-[#f0f0f0]"
          >
            {showIdealPoints ? "Hide ideal answer points" : "View ideal answer points"}
          </button>
          {showIdealPoints ? (
            <ul className="mt-3 space-y-2 text-sm text-[#bcbcbc]">
              {result.feedback.ideal_answer_points.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="text-[#6e6e6e]">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        {result.follow_up.recommended ? (
          <div className="rounded-sm border border-white/10 border-l-4 border-l-indigo-400 bg-[#151515] p-4">
            <div className="mb-3 font-mono text-xs uppercase tracking-[0.18em] text-indigo-300">
              Follow-up question
            </div>
            <p className="font-mono text-base leading-7 text-[#f0f0f0]">
              {result.follow_up.question_text}
            </p>
            <p className="mt-3 text-xs text-[#8f8f8f]">
              This would be the next question in a real interview
            </p>
          </div>
        ) : null}
      </div>

      <div className="mt-6 flex items-center justify-between gap-4 text-xs text-[#8f8f8f]">
        <span>Evaluated in {latencySeconds}s</span>
        {onEvaluateAgain ? (
          <button
            onClick={onEvaluateAgain}
            className="rounded-sm border border-white/10 px-3 py-1 text-[#cfcfcf] transition-colors hover:bg-white/5"
          >
            Evaluate Again
          </button>
        ) : null}
      </div>
    </section>
  );
}
