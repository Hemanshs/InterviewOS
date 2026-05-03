import type { TranscribeResult } from "@/types/interview";

interface TranscriptCardProps {
  result: TranscribeResult;
}

export function TranscriptCard({ result }: TranscriptCardProps) {
  const isEmpty = result.word_count === 0 || result.transcript.trim() === "";
  const latencySeconds = (result.latency.transcription_ms / 1000).toFixed(1);

  return (
    <section className="rounded-sm border border-white/10 border-l-4 border-l-cyan-400 bg-[#1a1a1a] p-6">
      <div className="mb-5 font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
        Your answer
      </div>

      {isEmpty ? (
        <p className="text-base text-[#d7d7d7]">
          No speech detected. Please try recording again.
        </p>
      ) : (
        <>
          <p className="whitespace-pre-wrap text-base leading-7 text-[#f0f0f0]">
            {result.transcript}
          </p>

          <div className="mt-5 flex flex-wrap gap-2">
            <span className="rounded-full border border-white/15 px-3 py-1 text-xs text-[#cfcfcf]">
              {result.word_count} words
            </span>
            <span className="rounded-full border border-white/15 px-3 py-1 text-xs text-[#cfcfcf]">
              {result.duration_seconds}s
            </span>
          </div>

          {result.filler_words.count > 0 ? (
            <div className="mt-6 space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-sm text-[#d8d8d8]">
                  Filler words detected
                </span>
                <span className="rounded-full border border-amber-500/40 px-2.5 py-0.5 text-xs text-amber-300">
                  {result.filler_words.count}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {result.filler_words.examples.map((example) => (
                  <span
                    key={example}
                    className="rounded-full border border-amber-500/30 px-3 py-1 text-xs text-amber-200"
                  >
                    {example}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <p className="mt-6 text-sm text-emerald-300">
              No filler words detected
            </p>
          )}
        </>
      )}

      <div className="mt-6 space-y-2 text-xs text-[#9c9c9c]">
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              result.raw_audio_deleted ? "bg-emerald-400" : "bg-amber-400"
            }`}
          />
          <span>
            {result.raw_audio_deleted
              ? "Audio deleted after transcription"
              : "Audio pending deletion"}
          </span>
        </div>
        <div>Transcribed in {latencySeconds}s</div>
      </div>
    </section>
  );
}
