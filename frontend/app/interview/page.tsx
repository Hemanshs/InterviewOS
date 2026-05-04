"use client";

import { AudioPlayer } from "@/components/AudioPlayer";
import { AnswerReview } from "@/components/AnswerReview";
import { EvaluationCard } from "@/components/EvaluationCard";
import { ErrorBox } from "@/components/ErrorBox";
import { FinalScorecard } from "@/components/FinalScorecard";
import { LatencyIndicator } from "@/components/LatencyIndicator";
import { MicRecorder } from "@/components/MicRecorder";
import { ProgressBar } from "@/components/ProgressBar";
import { QuestionCard } from "@/components/QuestionCard";
import { RecoveryBanner } from "@/components/RecoveryBanner";
import { ResumeProfileCard } from "@/components/ResumeProfileCard";
import { ResumeUploadCard } from "@/components/ResumeUploadCard";
import { TranscriptCard } from "@/components/TranscriptCard";
import { useInterview } from "@/hooks/useInterview";

export default function InterviewPage() {
  const {
    recoveryChecked,
    latencyState,
    question,
    transcript,
    evaluation,
    error,
    questionNumber,
    maxQuestions,
    completedAnswers,
    isInterviewComplete,
    finalReport,
    resumeProfile,
    resumeId,
    resumeFileName,
    session,
    setup,
    recoverableSession,
    activeContextLabel,
    updateSetup,
    startInterview,
    resumeRecovery,
    handleResumeUploaded,
    skipResume,
    discardRecovery,
    handleTranscriptReady,
    handleRecordingError,
    handleLatencyStateChange,
    submitEvaluation,
    loadNextQuestion,
    finishInterview,
    generateReport,
    reset,
    clearError,
  } = useInterview();

  const isLoading =
    latencyState === "question_generating" ||
    latencyState === "voice_generating" ||
    latencyState === "next_question_loading";

  if (!recoveryChecked) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6 py-12">
        <div className="w-full max-w-2xl space-y-6 text-center">
          <div className="space-y-3">
            <div className="font-mono text-xs uppercase tracking-[0.28em] text-[#8d8d8d]">
              Loading session
            </div>
            <h1 className="text-4xl tracking-tight text-[#f5f5f5] md:text-5xl">
              InterviewOS
            </h1>
            <p className="text-lg text-[#9a9a9a]">
              Restoring your interview state...
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="w-full max-w-2xl space-y-6">
        {recoverableSession && latencyState === "idle" ? (
          <RecoveryBanner
            sessionId={recoverableSession.session_id}
            interviewType={recoverableSession.interview_type}
            questionCount={recoverableSession.question_count}
            lastActivityAt={recoverableSession.started_at}
            onResume={resumeRecovery}
            onDiscard={discardRecovery}
            onStartNew={() => {
              discardRecovery();
            }}
          />
        ) : null}

        <div className="space-y-3 text-center">
          <div className="font-mono text-xs uppercase tracking-[0.28em] text-[#8d8d8d]">
            Phase 4.3 setup flow
          </div>
          <h1 className="text-4xl tracking-tight text-[#f5f5f5] md:text-5xl">
            InterviewOS
          </h1>
          <p className="text-lg text-[#9a9a9a]">
            AI Voice Interview Coach
          </p>
        </div>

        {latencyState === "idle" && !resumeProfile ? (
          <ResumeUploadCard
            onUploaded={handleResumeUploaded}
            onSkip={skipResume}
          />
        ) : null}

        {latencyState === "idle" && resumeProfile ? (
          <ResumeProfileCard
            profile={resumeProfile}
            fileName={resumeFileName || "resume.pdf"}
            onRemove={skipResume}
          />
        ) : null}

        {latencyState === "idle" ? (
          <div className="flex justify-center">
            <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-gray-500">
              {activeContextLabel}
            </span>
          </div>
        ) : null}

        {latencyState === "idle" ? (
          <section className="rounded-sm border border-white/10 bg-[#1a1a1a] px-5 py-5">
            <div className="mb-4 font-mono text-xs uppercase tracking-[0.22em] text-[#8d8d8d]">
              Interview setup
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="block text-xs font-mono uppercase tracking-[0.18em] text-[#8d8d8d]">
                  Job description
                </label>
                <textarea
                  value={setup.jobDescription}
                  onChange={(event) => updateSetup("jobDescription", event.target.value)}
                  rows={5}
                  placeholder="Paste the job description here (optional unless JD-based)"
                  className="w-full rounded-sm border border-white/10 bg-[#101010] px-4 py-3 text-sm text-[#f5f5f5] outline-none transition-colors placeholder:text-[#6f6f6f] focus:border-[#ff6b00]/50"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="block text-xs font-mono uppercase tracking-[0.18em] text-[#8d8d8d]">
                    Target role
                  </label>
                  <input
                    value={setup.targetRole}
                    onChange={(event) => updateSetup("targetRole", event.target.value)}
                    placeholder="Backend Engineer"
                    className="w-full rounded-sm border border-white/10 bg-[#101010] px-4 py-3 text-sm text-[#f5f5f5] outline-none transition-colors placeholder:text-[#6f6f6f] focus:border-[#ff6b00]/50"
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-xs font-mono uppercase tracking-[0.18em] text-[#8d8d8d]">
                    Target company
                  </label>
                  <input
                    value={setup.targetCompany}
                    onChange={(event) => updateSetup("targetCompany", event.target.value)}
                    placeholder="Amazon"
                    className="w-full rounded-sm border border-white/10 bg-[#101010] px-4 py-3 text-sm text-[#f5f5f5] outline-none transition-colors placeholder:text-[#6f6f6f] focus:border-[#ff6b00]/50"
                  />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="block text-xs font-mono uppercase tracking-[0.18em] text-[#8d8d8d]">
                    Interview type
                  </label>
                  <select
                    value={setup.interviewType}
                    onChange={(event) =>
                      updateSetup("interviewType", event.target.value as typeof setup.interviewType)
                    }
                    className="w-full rounded-sm border border-white/10 bg-[#101010] px-4 py-3 text-sm text-[#f5f5f5] outline-none transition-colors focus:border-[#ff6b00]/50"
                  >
                    <option value="sde">sde</option>
                    <option value="sdet">sdet</option>
                    <option value="backend">backend</option>
                    <option value="behavioral">behavioral</option>
                    <option value="system_design">system_design</option>
                    <option value="resume_based">resume_based</option>
                    <option value="jd_based">jd_based</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="block text-xs font-mono uppercase tracking-[0.18em] text-[#8d8d8d]">
                    Difficulty
                  </label>
                  <select
                    value={setup.difficulty}
                    onChange={(event) =>
                      updateSetup("difficulty", event.target.value as typeof setup.difficulty)
                    }
                    className="w-full rounded-sm border border-white/10 bg-[#101010] px-4 py-3 text-sm text-[#f5f5f5] outline-none transition-colors focus:border-[#ff6b00]/50"
                  >
                    <option value="easy">easy</option>
                    <option value="medium">medium</option>
                    <option value="hard">hard</option>
                  </select>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="block text-xs font-mono uppercase tracking-[0.18em] text-[#8d8d8d]">
                    Question count
                  </label>
                  <select
                    value={setup.questionCount}
                    onChange={(event) => updateSetup("questionCount", Number(event.target.value))}
                    className="w-full rounded-sm border border-white/10 bg-[#101010] px-4 py-3 text-sm text-[#f5f5f5] outline-none transition-colors focus:border-[#ff6b00]/50"
                  >
                    <option value={1}>1</option>
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                    <option value={4}>4</option>
                    <option value={5}>5</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="block text-xs font-mono uppercase tracking-[0.18em] text-[#8d8d8d]">
                    Voice
                  </label>
                  <button
                    type="button"
                    onClick={() => updateSetup("voiceEnabled", !setup.voiceEnabled)}
                    className={`flex w-full items-center justify-between rounded-sm border px-4 py-3 text-sm transition-colors ${
                      setup.voiceEnabled
                        ? "border-[#ff6b00]/50 bg-[#20150b] text-[#f5f5f5]"
                        : "border-white/10 bg-[#101010] text-[#9a9a9a]"
                    }`}
                  >
                    <span>{setup.voiceEnabled ? "Voice enabled" : "Voice disabled"}</span>
                    <span className="font-mono text-xs">
                      {setup.voiceEnabled ? "ON" : "OFF"}
                    </span>
                  </button>
                </div>
              </div>

              <div className="rounded-sm border border-white/10 bg-[#101010] px-4 py-3 text-xs font-mono text-[#8d8d8d]">
                Resume: {resumeId ? (resumeFileName || "Uploaded") : "Not uploaded"} · Role: {setup.targetRole.trim() || setup.interviewType} · Difficulty: {setup.difficulty}
              </div>

              <div className="flex justify-center pt-2">
                <button
                  onClick={startInterview}
                  disabled={isLoading}
                  className="rounded-sm border border-[#ff6b00] bg-[#ff6b00] px-8 py-3 font-semibold text-[#111111] transition-colors hover:bg-[#ff7d26] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Start Interview
                </button>
              </div>
            </div>
          </section>
        ) : null}

        {latencyState !== "idle" && !isInterviewComplete ? (
          <LatencyIndicator state={latencyState} />
        ) : null}

        {error ? <ErrorBox message={error} onDismiss={clearError} /> : null}

        {isInterviewComplete ? (
          <div className="space-y-6 py-12 text-center">
            <div className="text-6xl">✓</div>
            <h2 className="text-2xl font-bold">Interview Complete</h2>
            {isInterviewComplete && !finalReport && latencyState !== "final_report_generating" ? (
              <div className="space-y-4 text-center">
                <p className="text-gray-400 text-sm">
                  You answered {completedAnswers.length} of {maxQuestions} questions.
                </p>
                <button
                  onClick={generateReport}
                  className="rounded-xl bg-amber-400 px-10 py-4 text-lg font-semibold text-black transition-colors hover:bg-amber-300"
                >
                  Generate Final Scorecard
                </button>
              </div>
            ) : null}
            {latencyState === "final_report_generating" ? (
              <div className="space-y-3 py-8 text-center">
                <LatencyIndicator state="final_report_generating" />
                <p className="font-mono text-sm text-gray-500">
                  Analyzing your 5 answers...
                </p>
              </div>
            ) : null}
            {finalReport && latencyState === "scorecard_ready" ? (
              <FinalScorecard
                report={finalReport}
                completedAnswers={completedAnswers}
                onStartNew={reset}
              />
            ) : null}
            {error &&
            (latencyState === "interview_complete" || latencyState === "error") ? (
              <div className="space-y-3">
                <ErrorBox message={error} onDismiss={clearError} />
                <div className="flex justify-center">
                  <button
                    onClick={generateReport}
                    className="rounded-xl border border-amber-400/30 px-6 py-3 font-semibold text-amber-300 transition-colors hover:bg-amber-400/10"
                  >
                    Retry Scorecard
                  </button>
                </div>
              </div>
            ) : null}
            <AnswerReview answers={completedAnswers} />
          </div>
        ) : question && latencyState !== "idle" ? (
          <>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-gray-500">
                {activeContextLabel}
              </span>
              <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-gray-500">
                {session?.target_role || setup.targetRole || setup.interviewType}
              </span>
              <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-gray-500">
                {session?.difficulty || setup.difficulty}
              </span>
            </div>
            {questionNumber > 0 ? (
              <ProgressBar
                current={completedAnswers.length}
                total={maxQuestions}
                label={`Question ${questionNumber} of ${maxQuestions}`}
              />
            ) : null}
            <QuestionCard question={question} />
            <AudioPlayer
              audioUrl={question.audio.audio_url}
              enabled={question.audio.enabled}
              cached={question.audio.cached}
            />
            <MicRecorder
              questionId={question.question_id}
              sessionId={session?.session_id || ""}
              onTranscriptReady={handleTranscriptReady}
              onError={handleRecordingError}
              onStateChange={handleLatencyStateChange}
              disabled={transcript !== null || evaluation !== null}
            />
            {transcript ? (
              <TranscriptCard result={transcript} />
            ) : null}
            {transcript && !evaluation ? (
              <div className="flex justify-center">
                <button
                  onClick={submitEvaluation}
                  className="rounded-xl bg-amber-400 px-8 py-3 font-semibold text-black transition-colors hover:bg-amber-300"
                >
                  Evaluate Answer
                </button>
              </div>
            ) : null}
            {(latencyState === "evaluating_answer" ||
              latencyState === "preparing_follow_up") ? (
              <LatencyIndicator state={latencyState} />
            ) : null}
            {evaluation && latencyState === "evaluation_ready" ? (
              <EvaluationCard result={evaluation} />
            ) : null}
            {evaluation &&
            latencyState === "evaluation_ready" &&
            questionNumber < maxQuestions ? (
              <div className="flex justify-center">
                <button
                  onClick={loadNextQuestion}
                  className="rounded-xl bg-white px-8 py-3 font-semibold text-black transition-colors hover:bg-gray-100 disabled:opacity-50"
                >
                  Next Question →
                </button>
              </div>
            ) : null}
            {evaluation &&
            latencyState === "evaluation_ready" &&
            questionNumber === maxQuestions ? (
              <div className="flex justify-center">
                <button
                  onClick={finishInterview}
                  className="rounded-xl bg-green-600 px-8 py-3 font-semibold text-white transition-colors hover:bg-green-500"
                >
                  Finish Interview
                </button>
              </div>
            ) : null}
            {completedAnswers.length > 0 && !isInterviewComplete ? (
              <AnswerReview answers={completedAnswers} />
            ) : null}
            <div className="flex justify-center">
              <button
                onClick={reset}
                className="rounded-sm border border-white/15 px-6 py-2 text-sm text-[#c7c7c7] transition-colors hover:bg-white/5"
              >
                Reset
              </button>
            </div>
          </>
        ) : null}
      </div>
    </main>
  );
}
