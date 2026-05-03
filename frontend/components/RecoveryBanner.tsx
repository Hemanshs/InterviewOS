interface RecoveryBannerProps {
  sessionId: string;
  interviewType: string;
  questionCount: number;
  lastActivityAt: string;
  onResume: (sessionId: string) => void;
  onDiscard: () => void;
  onStartNew: () => void;
}

function formatTimeAgo(lastActivityAt: string): string {
  const timestamp = Date.parse(lastActivityAt);
  if (Number.isNaN(timestamp)) {
    return "recently";
  }

  const diffMs = Date.now() - timestamp;
  const diffMinutes = Math.max(1, Math.floor(diffMs / 60000));
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export function RecoveryBanner({
  sessionId,
  interviewType,
  questionCount,
  lastActivityAt,
  onResume,
  onDiscard,
  onStartNew,
}: RecoveryBannerProps) {
  return (
    <section className="w-full rounded-sm border border-amber-500/40 bg-amber-950/20 px-5 py-4">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-1">
          <div className="font-mono text-xs uppercase tracking-[0.22em] text-amber-300">
            Session Recovery
          </div>
          <p className="text-sm text-amber-100">
            You have an unfinished interview from {formatTimeAgo(lastActivityAt)}.
          </p>
          <p className="text-xs text-amber-200/80">
            {interviewType} · {questionCount} questions answered
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => onResume(sessionId)}
            className="rounded-sm bg-amber-400 px-4 py-2 text-sm font-semibold text-black transition-colors hover:bg-amber-300"
          >
            Resume Interview
          </button>
          <button
            type="button"
            onClick={onStartNew}
            className="rounded-sm border border-amber-400/40 px-4 py-2 text-sm font-semibold text-amber-100 transition-colors hover:border-amber-300 hover:text-amber-50"
          >
            Start New
          </button>
          <button
            type="button"
            onClick={onDiscard}
            className="px-2 py-2 text-sm text-amber-200/80 transition-colors hover:text-amber-50"
          >
            Discard
          </button>
        </div>
      </div>
    </section>
  );
}
