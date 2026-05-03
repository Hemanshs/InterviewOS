interface AudioPlayerProps {
  audioUrl: string | null;
  enabled: boolean;
  cached: boolean;
}

export function AudioPlayer({
  audioUrl,
  enabled,
  cached,
}: AudioPlayerProps) {
  const isMockUrl = audioUrl?.includes("mock-tts.interviewos.dev") ?? false;

  if (!enabled) {
    return (
      <div className="rounded-sm border border-white/10 bg-[#121212] px-4 py-3 text-sm text-[#a3a3a3]">
        Audio disabled for this question
      </div>
    );
  }

  if (!audioUrl) {
    return (
      <div className="rounded-sm border border-red-500/30 bg-[#121212] px-4 py-3 text-sm text-red-300">
        Voice generation failed — read the question above
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-sm border border-white/10 bg-[#121212] px-4 py-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#8d8d8d]">
        <span>Interviewer voice</span>
        {cached ? (
          <span className="rounded-full border border-emerald-500/40 px-2 py-0.5 text-[10px] tracking-[0.2em] text-emerald-300">
            Cached
          </span>
        ) : null}
      </div>
      <audio controls src={audioUrl} className="w-full" />
      {isMockUrl ? (
        <p className="text-sm text-[#9a9a9a]">
          Dev mode: mock audio URL — real audio available with ElevenLabs key
        </p>
      ) : null}
    </div>
  );
}
