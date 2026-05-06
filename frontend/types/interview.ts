export type InterviewMode = "first" | "next" | "follow_up";
export type InterviewType =
  | "sde"
  | "sdet"
  | "backend"
  | "behavioral"
  | "system_design"
  | "resume_based"
  | "jd_based";
export type InterviewDifficulty = "easy" | "medium" | "hard";

export type LatencyStateType =
  | "idle"
  | "question_generating"
  | "voice_generating"
  | "ready_for_answer"
  | "recording_answer"
  | "uploading_audio"
  | "transcribing_answer"
  | "transcript_ready"
  | "evaluating_answer"
  | "preparing_follow_up"
  | "evaluation_ready"
  | "next_question_loading"
  | "interview_complete"
  | "final_report_generating"
  | "scorecard_ready"
  | "error";

export interface AudioData {
  enabled: boolean;
  provider: "elevenlabs" | "browser" | null;
  audio_url: string | null;
  duration_seconds: number | null;
  cached: boolean;
  label: string;
  upgrade_required: boolean;
  browser_speech_text: string | null;
}

export interface QuestionDetail {
  question_id: string;
  sequence: number;
  type: string;
  difficulty: string;
  question_text: string;
  expected_focus_areas: string[];
  time_limit_seconds: number;
  audio: AudioData;
}

export interface LatencyState {
  current: string;
  completed_steps: string[];
}

export interface QuestionResponseData {
  session_id: string;
  question: QuestionDetail;
  latency_state: LatencyState;
}

export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  message: string;
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

export interface GenerateQuestionPayload {
  session_id: string;
  mode: InterviewMode;
  include_voice: boolean;
  previous_answer_id?: string;
  question_count?: number;
}

export interface StartInterviewPayload {
  resume_id?: string | null;
  interview_type: InterviewType;
  difficulty: InterviewDifficulty;
  job_description?: string | null;
  target_company?: string | null;
  target_role?: string | null;
  question_count: number;
  voice_enabled: boolean;
}

export interface SessionLimits {
  max_questions: number;
  max_answer_duration_seconds: number;
}

export interface SessionNextAction {
  type: string;
  endpoint: string;
}

export interface StartInterviewResult {
  session_id: string;
  resume_id: string | null;
  interview_type: InterviewType;
  difficulty: InterviewDifficulty;
  target_role: string | null;
  target_company: string | null;
  voice_enabled: boolean;
  question_count: number;
  status: string;
  started_at: string;
  limits: SessionLimits;
  next_action: SessionNextAction;
  expires_at: string | null;
}

export interface FillerWords {
  count: number;
  examples: string[];
}

export interface TranscribeLatency {
  transcription_ms: number;
}

export interface TranscribeResult {
  answer_id: string;
  session_id: string;
  question_id: string;
  transcript: string;
  language: string;
  duration_seconds: number;
  word_count: number;
  filler_words: FillerWords;
  raw_audio_deleted: boolean;
  submitted_at: string;
  latency: TranscribeLatency;
}

export interface TranscribePayload {
  session_id: string;
  question_id: string;
  duration_seconds: number;
  language?: string;
  audio_file: Blob;
}

export interface EvaluationScores {
  technical_correctness: number | null;
  clarity: number | null;
  depth: number | null;
  confidence: number | null;
  relevance: number | null;
  structure: number | null;
  communication: number | null;
  conciseness: number | null;
  example_quality: number | null;
  overall: number | null;
}

export interface EvaluationFeedback {
  summary: string;
  strengths: string[];
  improvements: string[];
  ideal_answer_points: string[];
}

export interface FollowUp {
  recommended: boolean;
  question_text: string | null;
}

export interface EvaluationLatency {
  evaluation_ms: number;
}

export interface EvaluateResult {
  score_id: string;
  session_id: string;
  question_id: string;
  answer_id: string;
  scores: EvaluationScores;
  feedback: EvaluationFeedback;
  follow_up: FollowUp;
  latency: EvaluationLatency;
}

export interface EvaluatePayload {
  session_id: string;
  question_id: string;
  answer_id: string;
  generate_follow_up: boolean;
}

export interface CompletedAnswer {
  questionNumber: number;
  questionId: string;
  questionText: string;
  questionType: string;
  answerId: string;
  transcript: string;
  wordCount: number;
  scores: EvaluationScores;
  overallScore: number | null;
  feedbackSummary: string;
  strengths: string[];
  improvements: string[];
}

export interface InterviewSession {
  sessionId: string;
  maxQuestions: number;
  completedAnswers: CompletedAnswer[];
  isComplete: boolean;
}

export interface FinalScoreBreakdown {
  technical: number;
  communication: number;
  confidence: number;
  problem_solving: number;
  role_fit: number;
}

export interface FinalQuestionReview {
  question_id: string;
  sequence: number;
  question_text: string;
  answer_id: string;
  overall_score: number;
  feedback_summary: string;
}

export interface FinalTranscriptItem {
  question: string;
  answer: string;
}

export interface FinalReport {
  report_id: string;
  session_id: string;
  status: string;
  overall_score: number;
  score_breakdown: FinalScoreBreakdown;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommended_topics: string[];
  question_reviews: FinalQuestionReview[];
  transcript: FinalTranscriptItem[] | null;
  created_at: string;
}

export interface FinalReportPayload {
  session_id: string;
  include_transcript: boolean;
  include_recommendations: boolean;
}

export interface SkillSet {
  languages: string[];
  frameworks: string[];
  databases: string[];
  cloud_devops: string[];
  testing_tools: string[];
  other: string[];
}

export interface ExperienceItem {
  company: string | null;
  role: string | null;
  start_date: string | null;
  end_date: string | null;
  responsibilities: string[];
  achievements: string[];
  technologies: string[];
}

export interface ProjectItem {
  name: string | null;
  description: string | null;
  technologies: string[];
  interview_focus: string[];
}

export interface ResumeProfile {
  candidate_name: string | null;
  email: string | null;
  current_or_latest_role: string | null;
  total_experience_years: number | null;
  summary: string | null;
  skills: SkillSet;
  experience: ExperienceItem[];
  projects: ProjectItem[];
  strength_areas: string[];
  recommended_interview_topics: string[];
}

export interface ResumeUploadResult {
  resume_id: string;
  file_name: string;
  parsed: boolean;
  profile: ResumeProfile | null;
  created_at: string;
}

export interface HistoryItem {
  session_id: string;
  interview_type: string;
  target_role: string | null;
  target_company: string | null;
  status: string;
  question_count: number;
  overall_score: number | null;
  started_at: string;
  ended_at: string | null;
}

export interface Pagination {
  page: number;
  limit: number;
  total_items: number;
  total_pages: number;
}

export interface HistoryData {
  items: HistoryItem[];
  pagination: Pagination;
}

export interface SessionDetailResult {
  session_id: string;
  resume_id: string | null;
  interview_type: InterviewType;
  difficulty: InterviewDifficulty;
  target_role: string | null;
  target_company: string | null;
  job_description: string | null;
  question_count: number;
  voice_enabled: boolean;
  status: string;
  started_at: string;
  expires_at: string | null;
  questions_answered: number;
  current_sequence: number;
  last_activity_at: string;
  resume_profile: ResumeProfile | null;
  current_question: QuestionDetail | null;
  current_transcript: TranscribeResult | null;
  current_evaluation: EvaluateResult | null;
  completed_answers: CompletedAnswer[];
  final_report: FinalReport | null;
}
