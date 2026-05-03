interface ErrorBoxProps {
  message: string;
  onDismiss: () => void;
}

export function ErrorBox({ message, onDismiss }: ErrorBoxProps) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-sm border border-red-500/40 bg-red-950/20 px-4 py-4 text-red-200">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 inline-flex h-6 w-6 items-center justify-center rounded-full border border-red-500/40 text-sm">
          !
        </span>
        <p className="text-sm leading-6">{message}</p>
      </div>
      <button
        onClick={onDismiss}
        className="rounded-sm border border-red-500/30 px-3 py-1 text-xs uppercase tracking-[0.16em] text-red-200 transition-colors hover:bg-red-500/10"
      >
        Dismiss
      </button>
    </div>
  );
}
