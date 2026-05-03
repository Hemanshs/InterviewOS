"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  evaluateAnswer,
  generateFinalReport,
  generateQuestion,
  getInterviewHistory,
  startInterviewSession,
} from "@/lib/api";
import type {
  CompletedAnswer,
  EvaluateResult,
  FinalReport,
  HistoryItem,
  InterviewDifficulty,
  InterviewType,
  LatencyStateType,
  QuestionDetail,
  ResumeProfile,
  ResumeUploadResult,
  StartInterviewResult,
  TranscribeResult,
} from "@/types/interview";

const MAX_QUESTIONS = 5;

interface SetupState {
  interviewType: InterviewType;
  difficulty: InterviewDifficulty;
  jobDescription: string;
  targetRole: string;
  targetCompany: string;
  questionCount: number;
  voiceEnabled: boolean;
}

const DEFAULT_SETUP: SetupState = {
  interviewType: "sde",
  difficulty: "medium",
  jobDescription: "",
  targetRole: "",
  targetCompany: "",
  questionCount: 5,
  voiceEnabled: true,
};

export function useInterview() {
  const [latencyState, setLatencyState] = useState<LatencyStateType>("idle");
  const [question, setQuestion] = useState<QuestionDetail | null>(null);
  const [transcript, setTranscript] = useState<TranscribeResult | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluateResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [completedAnswers, setCompletedAnswers] = useState<CompletedAnswer[]>([]);
  const [isInterviewComplete, setIsInterviewComplete] = useState(false);
  const [finalReport, setFinalReport] = useState<FinalReport | null>(null);
  const [resumeProfile, setResumeProfile] = useState<ResumeProfile | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [resumeFileName, setResumeFileName] = useState<string | null>(null);
  const [session, setSession] = useState<StartInterviewResult | null>(null);
  const [setup, setSetup] = useState<SetupState>(DEFAULT_SETUP);
  const [recoverableSession, setRecoverableSession] = useState<HistoryItem | null>(null);

  const activeContextLabel = useMemo(() => {
    if (session?.resume_id) {
      return `Resume-based${resumeProfile?.candidate_name ? ` · ${resumeProfile.candidate_name}` : ""}`;
    }
    if (setup.interviewType === "resume_based" && resumeProfile) {
      return `Resume-based${resumeProfile.candidate_name ? ` · ${resumeProfile.candidate_name}` : ""}`;
    }
    if (session?.interview_type === "jd_based" || (setup.interviewType === "jd_based" && setup.jobDescription.trim())) {
      return "JD-based";
    }
    if (setup.jobDescription.trim()) {
      return "Resume + JD";
    }
    return "No-resume";
  }, [resumeProfile, session, setup.interviewType, setup.jobDescription]);

  const updateSetup = useCallback(
    <K extends keyof SetupState>(field: K, value: SetupState[K]) => {
      setSetup((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const savedSessionId = window.localStorage.getItem("interviewos_session_id");
    if (!savedSessionId) {
      return;
    }

    getInterviewHistory("in_progress")
      .then((response) => {
        if (!response.success) {
          return;
        }
        const match = response.data.items.find(
          (item) => item.session_id === savedSessionId
        );
        if (match) {
          setRecoverableSession(match);
        }
      })
      .catch(() => {});
  }, []);

  const startInterview = useCallback(async () => {
    if (setup.interviewType === "jd_based" && !setup.jobDescription.trim()) {
      setError("Job description is required for JD-based interviews.");
      setLatencyState("error");
      return;
    }
    if (setup.interviewType === "resume_based" && !resumeId) {
      setError("Upload a resume before starting a resume-based interview.");
      setLatencyState("error");
      return;
    }

    setError(null);
    setQuestion(null);
    setTranscript(null);
    setEvaluation(null);
    setCompletedAnswers([]);
    setQuestionNumber(0);
    setIsInterviewComplete(false);
    setFinalReport(null);
    setSession(null);

    try {
      const sessionResponse = await startInterviewSession({
        resume_id: resumeId,
        interview_type: setup.interviewType,
        difficulty: setup.difficulty,
        job_description: setup.jobDescription.trim() || null,
        target_company: setup.targetCompany.trim() || null,
        target_role: setup.targetRole.trim() || null,
        question_count: Math.min(setup.questionCount, MAX_QUESTIONS),
        voice_enabled: setup.voiceEnabled,
      });

      if (!sessionResponse.success) {
        setSession(null);
        setError(sessionResponse.error.message);
        setLatencyState("error");
        return;
      }

      setSession(sessionResponse.data);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(
          "interviewos_session_id",
          sessionResponse.data.session_id
        );
      }
      setRecoverableSession(null);
      setLatencyState("question_generating");

      const response = await generateQuestion({
        session_id: sessionResponse.data.session_id,
        mode: "first",
        include_voice: sessionResponse.data.voice_enabled,
        question_count: sessionResponse.data.question_count,
      });

      if (!response.success) {
        setSession(null);
        setError(response.error.message);
        setLatencyState("error");
        return;
      }

      if (response.data.question.audio.enabled) {
        setLatencyState("voice_generating");
        await new Promise((resolve) => setTimeout(resolve, 400));
      }

      setQuestion(response.data.question);
      setQuestionNumber(1);
      setLatencyState("ready_for_answer");
    } catch (err) {
      setSession(null);
      setError(err instanceof Error ? err.message : "Failed to start interview");
      setLatencyState("error");
    }
  }, [resumeId, setup]);

  const handleTranscriptReady = useCallback((result: TranscribeResult) => {
    setTranscript(result);
    setLatencyState("transcript_ready");
  }, []);

  const handleRecordingError = useCallback((message: string) => {
    setError(message);
    setLatencyState("error");
  }, []);

  const handleLatencyStateChange = useCallback(
    (state: LatencyStateType) => {
      if (state === "ready_for_answer" && (transcript || evaluation)) {
        return;
      }
      setLatencyState(state);
    },
    [evaluation, transcript]
  );

  const submitEvaluation = useCallback(async () => {
    if (!transcript || !question || !session) {
      return;
    }
    setError(null);
    setLatencyState("evaluating_answer");

    try {
      const response = await evaluateAnswer({
        session_id: session.session_id,
        question_id: question.question_id,
        answer_id: transcript.answer_id,
        generate_follow_up: true,
      });

      if (!response.success) {
        setError(response.error.message);
        setLatencyState("error");
        return;
      }

      if (response.data.follow_up.recommended) {
        setLatencyState("preparing_follow_up");
        await new Promise((resolve) => setTimeout(resolve, 300));
      }

      setEvaluation(response.data);
      setLatencyState("evaluation_ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
      setLatencyState("error");
    }
  }, [question, session, transcript]);

  const loadNextQuestion = useCallback(async () => {
    if (!question || !transcript || !evaluation || !session) {
      return;
    }

    const nextNumber = questionNumber + 1;
    const completed: CompletedAnswer = {
      questionNumber,
      questionId: question.question_id,
      questionText: question.question_text,
      questionType: question.type,
      answerId: transcript.answer_id,
      transcript: transcript.transcript,
      wordCount: transcript.word_count,
      scores: evaluation.scores,
      overallScore: evaluation.scores.overall,
      feedbackSummary: evaluation.feedback.summary,
      strengths: evaluation.feedback.strengths,
      improvements: evaluation.feedback.improvements,
    };

    setCompletedAnswers((prev) => [...prev, completed]);

    if (nextNumber > MAX_QUESTIONS) {
      setIsInterviewComplete(true);
      setLatencyState("interview_complete");
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("interviewos_session_id");
      }
      setRecoverableSession(null);
      return;
    }

    setTranscript(null);
    setEvaluation(null);
    setError(null);
    setQuestion(null);
    setLatencyState("next_question_loading");

    try {
      const response = await generateQuestion({
        session_id: session.session_id,
        mode: "next",
        previous_answer_id: transcript.answer_id,
        include_voice: session.voice_enabled,
        question_count: session.question_count,
      });

      if (!response.success) {
        if (response.error.code === "RATE_LIMIT_EXCEEDED") {
          setIsInterviewComplete(true);
          setLatencyState("interview_complete");
          if (typeof window !== "undefined") {
            window.localStorage.removeItem("interviewos_session_id");
          }
          setRecoverableSession(null);
          return;
        }
        setError(response.error.message);
        setLatencyState("error");
        return;
      }

      if (response.data.question.audio.enabled) {
        setLatencyState("voice_generating");
        await new Promise((resolve) => setTimeout(resolve, 400));
      }

      setQuestion(response.data.question);
      setQuestionNumber(nextNumber);
      setLatencyState("ready_for_answer");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load next question");
      setLatencyState("error");
    }
  }, [evaluation, question, questionNumber, session, transcript]);

  const finishInterview = useCallback(() => {
    if (!question || !transcript || !evaluation) {
      setIsInterviewComplete(true);
      setLatencyState("interview_complete");
      return;
    }

    const completed: CompletedAnswer = {
      questionNumber,
      questionId: question.question_id,
      questionText: question.question_text,
      questionType: question.type,
      answerId: transcript.answer_id,
      transcript: transcript.transcript,
      wordCount: transcript.word_count,
      scores: evaluation.scores,
      overallScore: evaluation.scores.overall,
      feedbackSummary: evaluation.feedback.summary,
      strengths: evaluation.feedback.strengths,
      improvements: evaluation.feedback.improvements,
    };
    setCompletedAnswers((prev) => [...prev, completed]);
    setIsInterviewComplete(true);
    setLatencyState("interview_complete");
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("interviewos_session_id");
    }
    setRecoverableSession(null);
  }, [evaluation, question, questionNumber, transcript]);

  const generateReport = useCallback(async () => {
    if (!session) {
      return;
    }

    setError(null);
    setLatencyState("final_report_generating");

    try {
      const response = await generateFinalReport({
        session_id: session.session_id,
        include_transcript: true,
        include_recommendations: true,
      });

      if (!response.success) {
        setError(response.error.message);
        setLatencyState("interview_complete");
        return;
      }

      setFinalReport(response.data);
      setLatencyState("scorecard_ready");
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("interviewos_session_id");
      }
      setRecoverableSession(null);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate report. Please try again."
      );
      setLatencyState("interview_complete");
    }
  }, [session]);

  const clearError = useCallback(() => {
    setError(null);
    if (latencyState === "error" && !question && !session) {
      setLatencyState("idle");
    }
  }, [latencyState, question, session]);

  const handleResumeUploaded = useCallback((result: ResumeUploadResult) => {
    setResumeId(result.resume_id);
    setResumeFileName(result.file_name);
    setResumeProfile(result.profile);
  }, []);

  const skipResume = useCallback(() => {
    setResumeId(null);
    setResumeFileName(null);
    setResumeProfile(null);
  }, []);

  const discardRecovery = useCallback(() => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("interviewos_session_id");
    }
    setRecoverableSession(null);
  }, []);

  const reset = useCallback(() => {
    setLatencyState("idle");
    setQuestion(null);
    setTranscript(null);
    setEvaluation(null);
    setError(null);
    setQuestionNumber(0);
    setCompletedAnswers([]);
    setIsInterviewComplete(false);
    setFinalReport(null);
    setSession(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("interviewos_session_id");
    }
    setRecoverableSession(null);
  }, []);

  return {
    latencyState,
    question,
    transcript,
    evaluation,
    error,
    questionNumber,
    maxQuestions: session?.question_count ?? setup.questionCount ?? MAX_QUESTIONS,
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
    reset,
    clearError,
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
  };
}
