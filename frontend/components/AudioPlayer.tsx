import { useEffect, useRef, useState } from "react";

const STOP_AUDIO_EVENT = "interviewos-stop-question-audio";

interface AudioPlayerProps {
  audioUrl: string | null;
  enabled: boolean;
  cached: boolean;
  provider: "elevenlabs" | "browser" | null;
  label: string;
  upgradeRequired: boolean;
  browserSpeechText?: string | null;
  questionText?: string;
}

type PlaybackMode = "none" | "audio" | "browser";

export function AudioPlayer({
  audioUrl,
  enabled,
  cached,
  provider,
  label,
  upgradeRequired,
  browserSpeechText,
  questionText,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playbackModeRef = useRef<PlaybackMode>("none");
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasPlayed, setHasPlayed] = useState(false);
  const [standardVoiceSupported, setStandardVoiceSupported] = useState(false);

  useEffect(() => {
    setStandardVoiceSupported(
      typeof window !== "undefined" &&
        "speechSynthesis" in window &&
        typeof window.SpeechSynthesisUtterance !== "undefined"
    );
  }, []);

  const stopPlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    playbackModeRef.current = "none";
    setIsPlaying(false);
  };

  const speakStandardVoice = () => {
    const text = browserSpeechText || questionText;
    if (!standardVoiceSupported || !text) {
      return;
    }

    stopPlayback();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;

    const englishVoice =
      window.speechSynthesis
        .getVoices()
        .find((voice) => voice.lang.toLowerCase().startsWith("en")) ?? null;
    if (englishVoice) {
      utterance.voice = englishVoice;
    }

    utterance.onstart = () => {
      playbackModeRef.current = "browser";
      setHasPlayed(true);
      setIsPlaying(true);
    };
    utterance.onend = () => {
      if (playbackModeRef.current === "browser") {
        playbackModeRef.current = "none";
      }
      setIsPlaying(false);
    };
    utterance.onerror = () => {
      if (playbackModeRef.current === "browser") {
        playbackModeRef.current = "none";
      }
      setIsPlaying(false);
    };
    window.speechSynthesis.speak(utterance);
  };

  const playPremiumVoice = async () => {
    if (!audioUrl) {
      if (provider === "browser") {
        speakStandardVoice();
      }
      return;
    }

    stopPlayback();

    if (!audioRef.current) {
      audioRef.current = new Audio(audioUrl);
    } else if (audioRef.current.src !== audioUrl) {
      audioRef.current.src = audioUrl;
    }

    try {
      playbackModeRef.current = "audio";
      setHasPlayed(true);
      await audioRef.current.play();
    } catch {
      playbackModeRef.current = "none";
      if (provider === "browser") {
        speakStandardVoice();
      }
    }
  };

  const playVoice = async () => {
    if (!enabled) {
      return;
    }

    if (provider === "browser") {
      speakStandardVoice();
      return;
    }

    await playPremiumVoice();
  };

  useEffect(() => {
    if (!audioRef.current) {
      return;
    }

    const element = audioRef.current;
    const handlePlaying = () => {
      if (playbackModeRef.current === "audio") {
        setIsPlaying(true);
      }
    };
    const handleEnded = () => {
      if (playbackModeRef.current === "audio") {
        playbackModeRef.current = "none";
      }
      setIsPlaying(false);
    };
    const handlePause = () => {
      if (playbackModeRef.current === "audio") {
        setIsPlaying(false);
      }
    };

    element.addEventListener("playing", handlePlaying);
    element.addEventListener("ended", handleEnded);
    element.addEventListener("pause", handlePause);

    return () => {
      element.removeEventListener("playing", handlePlaying);
      element.removeEventListener("ended", handleEnded);
      element.removeEventListener("pause", handlePause);
    };
  }, [audioUrl]);

  useEffect(() => {
    setHasPlayed(false);
    setIsPlaying(false);
    playbackModeRef.current = "none";

    if (!enabled) {
      stopPlayback();
      return;
    }

    void playVoice();
    // autoplay best-effort when a new question arrives
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioUrl, browserSpeechText, enabled, provider, questionText, standardVoiceSupported]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const handleStop = () => stopPlayback();
    window.addEventListener(STOP_AUDIO_EVENT, handleStop);
    return () => {
      window.removeEventListener(STOP_AUDIO_EVENT, handleStop);
      stopPlayback();
    };
  }, []);

  if (!enabled) {
    return null;
  }

  const isStandardVoice = provider === "browser";
  const title = label || (isStandardVoice ? "Standard Voice" : "Premium AI Voice");

  return (
    <div className="space-y-3 rounded-sm border border-white/10 bg-[#121212] px-4 py-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#8d8d8d]">
        <span>Interviewer voice</span>
        <span className="rounded-full border border-[#ff6b00]/40 px-2 py-0.5 text-[10px] tracking-[0.2em] text-[#f3c28a]">
          {title}
        </span>
        {cached ? (
          <span className="rounded-full border border-emerald-500/40 px-2 py-0.5 text-[10px] tracking-[0.2em] text-emerald-300">
            Cached
          </span>
        ) : null}
      </div>

      {isPlaying ? (
        <div className="flex items-center gap-3">
          <div className="text-sm text-[#d8d8d8]">Question playing...</div>
          <button
            type="button"
            onClick={stopPlayback}
            className="rounded-sm border border-red-500/40 px-3 py-2 text-sm text-red-300 transition-colors hover:bg-red-500/10"
          >
            Stop
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => void playVoice()}
            className="rounded-sm border border-[#ff6b00]/50 bg-[#20150b] px-4 py-2 text-sm text-[#f5f5f5] transition-colors hover:bg-[#2b1b0e]"
          >
            {hasPlayed
              ? isStandardVoice
                ? "Replay Standard Voice"
                : "Replay Premium AI Voice"
              : isStandardVoice
                ? "Play Standard Voice"
                : "Play Premium AI Voice"}
          </button>
          {isStandardVoice && !standardVoiceSupported ? (
            <div className="text-sm text-[#d8d8d8]">
              Standard Voice is not supported in this browser. You can continue in text mode.
            </div>
          ) : null}
        </div>
      )}

      {upgradeRequired ? (
        <div className="text-sm text-[#b7b7b7]">
          Upgrade to Pro for Premium AI Voice on every question.
        </div>
      ) : null}
    </div>
  );
}
