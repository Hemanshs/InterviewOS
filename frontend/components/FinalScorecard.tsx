"use client";

import { useEffect, useMemo, useState } from "react";

import type {
  CompletedAnswer,
  FinalReport,
  FinalScoreBreakdown,
} from "@/types/interview";

interface FinalScorecardProps {
  report: FinalReport;
  completedAnswers: CompletedAnswer[];
  onStartNew: () => void;
}

const BREAKDOWN_LABELS: Record<keyof FinalScoreBreakdown, string> = {
  technical: "Technical",
  communication: "Communication",
  confidence: "Confidence",
  problem_solving: "Problem Solving",
  role_fit: "Role Fit",
};

function getScoreColor(score: number) {
  if (score >= 8) {
    return {
      text: "text-emerald-300",
      border: "border-emerald-500/40",
      bg: "bg-emerald-500",
    };
  }
  if (score >= 6.5) {
    return {
      text: "text-amber-300",
      border: "border-amber-500/40",
      bg: "bg-amber-400",
    };
  }
  return {
    text: "text-red-300",
    border: "border-red-500/40",
    bg: "bg-red-500",
  };
}

function formatDate(dateString: string) {
  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(dateString));
}

export function FinalScorecard({
  report,
  completedAnswers,
  onStartNew,
}: FinalScorecardProps) {
  const [showTranscript, setShowTranscript] = useState(false);
  const [showReviews, setShowReviews] = useState(true);
  const [animateBars, setAnimateBars] = useState(false);

  useEffect(() => {
    const id = window.setTimeout(() => setAnimateBars(true), 50);
    return () => window.clearTimeout(id);
  }, []);

  const overallStyle = getScoreColor(report.overall_score);
  const breakdownEntries = useMemo(
    () => Object.entries(report.score_breakdown) as Array<[keyof FinalScoreBreakdown, number]>,
    [report.score_breakdown]
  );

  return (
    <section className="space-y-8 rounded-sm border border-white/10 bg-[#121212] p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
            Interview scorecard
          </div>
          <div className="text-sm text-[#8f8f8f]">
            {formatDate(report.created_at)}
          </div>
        </div>
        <span className="rounded-full border border-emerald-500/40 px-3 py-1 text-xs font-mono uppercase tracking-[0.18em] text-emerald-300">
          {report.status}
        </span>
      </div>

      <div className="space-y-4 text-center">
        <div className={`mx-auto flex h-52 w-52 items-center justify-center rounded-full border-2 ${overallStyle.border}`}>
          <div>
            <div className={`font-mono text-8xl leading-none ${overallStyle.text}`}>
              {report.overall_score.toFixed(1)}
            </div>
            <div className="mt-2 text-sm uppercase tracking-[0.2em] text-[#8f8f8f]">
              out of 10
            </div>
          </div>
        </div>
        <p className="mx-auto max-w-2xl text-base leading-7 text-[#e8e8e8]">
          {report.summary}
        </p>
      </div>

      <div className="space-y-4">
        {breakdownEntries.map(([key, score], index) => {
          const style = getScoreColor(score);
          return (
            <div key={key} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#d8d8d8]">{BREAKDOWN_LABELS[key]}</span>
                <span className={`font-mono ${style.text}`}>{score.toFixed(1)}</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-[#1a1a1a]">
                <div
                  className={`h-full transition-all duration-700 ${style.bg}`}
                  style={{
                    width: animateBars ? `${(score / 10) * 100}%` : "0%",
                    transitionDelay: `${index * 100}ms`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-3">
          <h3 className="font-mono text-xs uppercase tracking-[0.22em] text-emerald-300">
            Strengths
          </h3>
          <ul className="space-y-2 text-sm text-[#d8d8d8]">
            {report.strengths.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-emerald-300">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="space-y-3">
          <h3 className="font-mono text-xs uppercase tracking-[0.22em] text-amber-300">
            Areas to improve
          </h3>
          <ul className="space-y-2 text-sm text-[#d8d8d8]">
            {report.weaknesses.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-amber-300">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="font-mono text-xs uppercase tracking-[0.22em] text-cyan-300">
          Study recommendations
        </h3>
        <div className="flex flex-wrap gap-2">
          {report.recommended_topics.map((topic) => (
            <span
              key={topic}
              className="rounded-full border border-cyan-500/30 px-3 py-1 text-xs text-cyan-200"
            >
              {topic}
            </span>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <h3 className="font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
            Question review
          </h3>
          <button
            onClick={() => setShowReviews((prev) => !prev)}
            className="rounded-sm border border-white/10 px-3 py-1 text-xs text-[#cfcfcf] transition-colors hover:bg-white/5"
          >
            {showReviews ? "Hide" : "Show"}
          </button>
        </div>
        {showReviews ? (
          <div className="divide-y divide-white/10 rounded-sm border border-white/10 bg-[#171717]">
            {report.question_reviews.map((item) => {
              const scoreStyle = getScoreColor(item.overall_score);
              return (
                <div key={item.answer_id} className="space-y-2 px-4 py-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm text-[#ececec]">
                      <span className="font-mono text-xs uppercase tracking-[0.16em] text-[#8d8d8d]">
                        Q{item.sequence}
                      </span>
                      <span>{item.question_text.length > 100 ? `${item.question_text.slice(0, 100)}...` : item.question_text}</span>
                    </div>
                    <span className={`rounded-full border px-2.5 py-0.5 text-xs font-mono ${scoreStyle.border} ${scoreStyle.text}`}>
                      {item.overall_score.toFixed(1)}
                    </span>
                  </div>
                  <p className="text-sm text-[#9d9d9d]">{item.feedback_summary}</p>
                </div>
              );
            })}
          </div>
        ) : null}
      </div>

      {report.transcript ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <h3 className="font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
              Full transcript
            </h3>
            <button
              onClick={() => setShowTranscript((prev) => !prev)}
              className="rounded-sm border border-white/10 px-3 py-1 text-xs text-[#cfcfcf] transition-colors hover:bg-white/5"
            >
              {showTranscript ? "Hide transcript" : "Show transcript"}
            </button>
          </div>
          {showTranscript ? (
            <div className="space-y-4 rounded-sm border border-white/10 bg-[#151515] px-4 py-4 font-mono text-sm text-[#bcbcbc]">
              {report.transcript.map((item, index) => (
                <div key={`${item.question}-${index}`} className="space-y-2 border-b border-white/10 pb-4 last:border-b-0 last:pb-0">
                  <div className="text-[#f1f1f1]">Q: {item.question}</div>
                  <div className="text-[#9e9e9e]">A: {item.answer}</div>
                </div>
              ))}
              <p className="text-xs text-[#7d7d7d]">
                Transcript from mock data — real transcript available with full LLM pipeline
              </p>
            </div>
          ) : null}
        </div>
      ) : null}

      {completedAnswers.length > 0 ? (
        <div className="rounded-sm border border-white/10 bg-[#171717] px-4 py-4 text-sm text-[#a8a8a8]">
          Local session context: {completedAnswers.length} answered question{completedAnswers.length === 1 ? "" : "s"} in this mock interview.
        </div>
      ) : null}

      <div className="flex justify-center">
        <button
          onClick={onStartNew}
          className="rounded-sm border border-white/15 px-6 py-2 text-sm text-[#d0d0d0] transition-colors hover:bg-white/5"
        >
          Start New Interview
        </button>
      </div>
    </section>
  );
}
