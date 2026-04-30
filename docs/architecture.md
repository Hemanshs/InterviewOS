# InterviewOS — Architecture Document

**Product:** AI Voice Interview Coach  
**Version:** v1.1  
**Scope:** MVP Architecture  
**Status:** Updated before coding

---

## 1. Overview

InterviewOS is a voice-based AI mock interview platform for software engineering candidates. The system combines resume parsing, LLM-driven question generation, voice interaction via ElevenLabs, speech-to-text transcription via Whisper/STT, and structured answer evaluation to simulate realistic technical interviews.

---

## 2. High-Level Architecture

The system is composed of four main layers:

```text
Frontend: Next.js browser app with mic recording and audio playback
Backend: FastAPI service housing business logic and integrations
Database & Storage: PostgreSQL/Supabase for structured data, S3/R2/Supabase Storage for files
External APIs: OpenAI/Claude, Whisper/STT, ElevenLabs
```

---

## 2.1 Architecture Diagram

```text
┌─────────────────────────────────────────────────────┐
│               USER (Browser)                        │
│  Next.js · MediaRecorder API · Audio Playback       │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS / REST
┌──────────────────▼──────────────────────────────────┐
│              FastAPI Backend                         │
│                                                     │
│  resume routes · interview routes · audio routes    │
│  feedback routes · account routes · usage routes    │
│                                                     │
│  resume_parser · llm_service · speech_service       │
│  voice_service · evaluation_service · usage_service │
└──────┬────────────────────┬────────────────┬────────┘
       │                    │                │
 ┌─────▼──────┐  ┌──────────▼──────┐  ┌─────▼──────────┐
 │ PostgreSQL │  │  External APIs  │  │ File Storage   │
 │ (Supabase) │  │ OpenAI / Claude │  │  S3 / R2       │
 │            │  │ Whisper STT     │  │  resume PDFs   │
 │ users      │  │ ElevenLabs TTS  │  │  temp audio    │
 │ resumes    │  └─────────────────┘  └────────────────┘
 │ sessions   │
 │ questions  │
 │ answers    │
 │ scores     │
 │ reports    │
 │ usage      │
 └────────────┘
```

---

## 3. Component Breakdown

### 3.1 Frontend Components

| Component | Responsibility |
|---|---|
| `InterviewSession` | Main interview UI — question playback, mic recording, progress states |
| `ResumeUpload` | Drag-and-drop PDF upload with validation |
| `ScoreCard` | Final report — scores, feedback, transcript |
| `Dashboard` | Interview history, past scorecards, progress tracking |
| `AudioPlayer` | Plays ElevenLabs-generated voice questions |
| `MicRecorder` | Browser mic capture via MediaRecorder API |
| `LatencyStates` | Animated progress steps during STT → LLM → TTS pipeline |
| `SessionRecoveryBanner` | Shows recoverable in-progress session after browser close/reload |

### 3.2 Backend Services

| Service | File | Responsibility |
|---|---|---|
| Interview routes | `routes/interview.py` | Start session, generate questions, evaluate answers, final report |
| Resume routes | `routes/resume.py` | Upload, parse, and store resume data |
| Audio routes | `routes/audio.py` | Accept audio blob, return transcript |
| Feedback routes | `routes/feedback.py` | Serve scorecard and per-question feedback |
| Account routes | `routes/account.py` | Account deletion and user data deletion |
| Usage routes | `routes/usage.py` | Usage status and quota information |
| LLM service | `services/llm_service.py` | Calls OpenAI/Claude for question generation and evaluation |
| Speech service | `services/speech_service.py` | Calls Whisper/STT for transcription |
| Voice service | `services/voice_service.py` | Calls ElevenLabs for TTS audio |
| Resume parser | `services/resume_parser.py` | Extracts structured data from PDF via PyMuPDF + LLM |
| Evaluation service | `services/evaluation_service.py` | Scores answers and builds final scorecards |
| Usage service | `services/usage_service.py` | Enforces rate limits and cost controls |

---

## 4. Data Flow — Full Interview Session

```text
1.  User logs in
2.  User uploads resume and/or enters job description
3.  Backend parses resume and extracts skills, experience, projects
4.  Backend analyzes JD if present
5.  LLM generates first interview question
6.  ElevenLabs converts question text to audio
7.  Frontend plays audio to user
8.  User answers via microphone
9.  Audio blob sent to /api/audio/transcribe
10. STT returns text transcript
11. Raw audio is deleted
12. LLM evaluates transcript against question
13. LLM generates follow-up or next question
14. Steps repeat until interview ends
15. Final scorecard is generated and stored in reports table
```

---

## 5. Latency Strategy

The STT → LLM → TTS pipeline introduces delay per turn. This is handled with progressive UI states:

```text
Transcribing your answer...
Evaluating your response...
Preparing next question...
Generating interviewer voice...
```

Post-MVP:

```text
Streaming LLM response
Chunked TTS
SSE/WebSocket progress events
```

---

# 6. Database Schema

---

## 6.1 `users`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `email` | TEXT | Unique |
| `created_at` | TIMESTAMP | Account creation time |
| `plan` | ENUM | `free`, `pro`, `team` |
| `free_interview_used` | BOOLEAN | True after user's one signup free interview is completed or started |
| `interviews_today` | INT | Development/demo rate-limit counter; not the main product free-tier rule |
| `deleted_at` | TIMESTAMP | Soft delete timestamp, nullable |

---

## 6.2 `resumes`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Foreign key → users |
| `file_name` | TEXT | Original filename |
| `file_url` | TEXT | Private storage URL |
| `parsed_profile` | JSONB | Structured resume extraction |
| `created_at` | TIMESTAMP | Upload time |
| `deleted_at` | TIMESTAMP | Soft delete timestamp, nullable |

---

## 6.3 `sessions`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Foreign key → users |
| `resume_id` | UUID | Foreign key → resumes, nullable for no-resume interview |
| `interview_type` | TEXT | `sde`, `sdet`, `backend`, `behavioral`, etc. |
| `difficulty` | TEXT | `easy`, `medium`, `hard` |
| `target_role` | TEXT | Optional target role |
| `target_company` | TEXT | Optional target company |
| `job_description` | TEXT | Optional JD text |
| `status` | ENUM | `in_progress`, `completed`, `abandoned`, `expired` |
| `current_sequence` | INT | Current question number |
| `started_at` | TIMESTAMP | Session start time |
| `last_activity_at` | TIMESTAMP | Used for browser-close/session recovery |
| `ended_at` | TIMESTAMP | Nullable |
| `expires_at` | TIMESTAMP | Auto-expiry timestamp for incomplete sessions |

---

## 6.4 `questions`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `session_id` | UUID | Foreign key → sessions |
| `sequence` | INT | Question order |
| `question_text` | TEXT | LLM-generated question |
| `question_type` | TEXT | `technical`, `behavioral`, `resume_deep_dive`, etc. |
| `expected_focus_areas` | JSONB | Expected answer focus points |
| `audio_url` | TEXT | ElevenLabs output URL, nullable |
| `prompt_version` | TEXT | Prompt version used to generate question |
| `created_at` | TIMESTAMP | Creation time |

---

## 6.5 `answers`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `question_id` | UUID | Foreign key → questions |
| `session_id` | UUID | Foreign key → sessions |
| `transcript` | TEXT | STT output |
| `duration_seconds` | INT | User answer duration |
| `word_count` | INT | Transcript word count |
| `filler_word_count` | INT | Basic communication metric |
| `raw_audio_deleted` | BOOLEAN | True after transcription |
| `submitted_at` | TIMESTAMP | Submission time |

---

## 6.6 `scores`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `session_id` | UUID | Foreign key → sessions |
| `question_id` | UUID | Foreign key → questions |
| `answer_id` | UUID | Foreign key → answers |
| `technical_score` | INT | 0–10 |
| `clarity_score` | INT | 0–10 |
| `depth_score` | INT | 0–10 |
| `confidence_score` | INT | 0–10 |
| `relevance_score` | INT | 0–10 |
| `structure_score` | INT | 0–10 |
| `communication_score` | INT | 0–10 |
| `conciseness_score` | INT | 0–10 |
| `example_quality_score` | INT | 0–10 |
| `overall_score` | DECIMAL | Per-answer overall score |
| `feedback_json` | JSONB | Structured feedback |
| `feedback_text` | TEXT | Human-readable feedback |
| `prompt_version` | TEXT | Prompt version used to evaluate answer |
| `created_at` | TIMESTAMP | Evaluation time |

---

## 6.7 `reports`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `session_id` | UUID | Foreign key → sessions |
| `user_id` | UUID | Foreign key → users |
| `overall_score` | DECIMAL | Final interview score |
| `score_breakdown` | JSONB | Technical, communication, confidence, role fit, etc. |
| `summary` | TEXT | Final report summary |
| `strengths` | JSONB | Strength list |
| `weaknesses` | JSONB | Weakness list |
| `recommended_topics` | JSONB | Recommended revision topics |
| `question_reviews` | JSONB | Question-by-question summaries |
| `transcript` | JSONB | Optional full transcript |
| `prompt_version` | TEXT | Prompt version used to generate final report |
| `created_at` | TIMESTAMP | Report creation time |
| `deleted_at` | TIMESTAMP | Soft delete timestamp, nullable |

---

## 6.8 `usage_events`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Foreign key → users |
| `session_id` | UUID | Foreign key → sessions, nullable |
| `event_type` | TEXT | `resume_parse`, `question_generation`, `tts_generation`, etc. |
| `model_name` | TEXT | AI model/provider used |
| `input_tokens` | INT | Nullable |
| `output_tokens` | INT | Nullable |
| `audio_duration_seconds` | INT | Nullable |
| `estimated_cost_usd` | DECIMAL | Estimated cost |
| `created_at` | TIMESTAMP | Event time |

---

# 7. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/me` | Current user profile |
| `DELETE` | `/api/account` | Delete account and user data |
| `POST` | `/api/resume/upload` | Upload and parse resume PDF |
| `GET` | `/api/resume/latest` | Get latest parsed resume |
| `DELETE` | `/api/resume/{resume_id}` | Delete resume |
| `POST` | `/api/interview/start` | Create session, set type and JD |
| `POST` | `/api/interview/question` | Generate next question + TTS audio |
| `POST` | `/api/audio/transcribe` | Submit audio blob, receive transcript |
| `POST` | `/api/interview/evaluate` | Evaluate answer, return score + feedback |
| `POST` | `/api/interview/final-report` | Generate and store final scorecard |
| `GET` | `/api/interview/history` | Fetch past sessions for dashboard |
| `GET` | `/api/interview/{session_id}` | Fetch session details |
| `GET` | `/api/interview/{session_id}/scorecard` | Fetch full scorecard |
| `POST` | `/api/interview/{session_id}/complete` | Complete active session |
| `DELETE` | `/api/interview/{session_id}` | Delete interview session |
| `GET` | `/api/usage` | Fetch usage/quota status |

---

# 8. Free Tier Rule

The MVP product rule is:

```text
Each registered free user gets 1 full free interview after signup.
```

Free interview includes:

```text
5 questions
60 seconds per answer
1 resume stored
Basic scorecard
```

After the one free interview is used:

```text
User must upgrade or wait for manually granted demo credits.
```

Development/demo environments may use configurable daily limits through env variables, but the product free-tier rule remains one full free interview per user.

---

# 9. Session Recovery

If the browser closes or reloads mid-interview:

```text
Session remains in_progress until expires_at
Backend updates last_activity_at on every meaningful action
Frontend checks GET /api/interview/history or GET /api/interview/{session_id}
If recoverable, show "Resume interview?" banner
User can resume from the last unanswered question
If session is older than expiry window, mark as expired
```

Default expiry:

```text
30 minutes of inactivity for MVP
```

---

# 10. Security & Privacy

```text
JWT-based auth on protected routes
User-scoped access to resumes, sessions, reports
Raw audio deleted after transcription
Private storage buckets for resumes and generated audio
No user voice cloning in MVP
User consent required before mic recording
DELETE /api/account for user data deletion
API keys stored only in environment variables
```

---

# 11. Deployment Architecture

```text
Vercel: Next.js frontend
Render/Railway/Fly.io: FastAPI backend
Supabase: Auth + PostgreSQL
S3/R2/Supabase Storage: files
OpenAI/Claude: LLM
Whisper/STT: transcription
ElevenLabs: interviewer voice
```

---

# 12. Post-MVP Roadmap

| Feature | Why it matters |
|---|---|
| Streaming TTS + chunked LLM | Reduce perceived latency |
| Company-specific interview mode | Higher-intent preparation |
| DSA + System Design modes | Expand technical depth |
| Voice confidence analysis | Unique voice-first feature |
| Progress tracking dashboard | Retention |
| Developer API | B2B/white-label use |
| Shareable scorecard | Growth loop |
