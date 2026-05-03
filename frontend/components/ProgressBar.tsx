"use client";

interface ProgressBarProps {
  current: number;
  total: number;
  label?: string;
}

export function ProgressBar({ current, total, label }: ProgressBarProps) {
  const percent = Math.min(100, Math.max(0, (current / total) * 100));
  const isComplete = current === total;

  return (
    <section className="space-y-3 rounded-sm border border-white/10 bg-[#121212] px-4 py-4">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-mono text-[#d7d7d7]">
          {isComplete ? "All questions answered" : label ?? `Question ${current} of ${total}`}
        </span>
        <span className="text-[#8e8e8e]">
          {isComplete ? "Complete" : `${current} answered`}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#232323]">
        <div
          className={`h-full transition-all duration-500 ${isComplete ? "bg-emerald-500" : "bg-amber-400"}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </section>
  );
}
