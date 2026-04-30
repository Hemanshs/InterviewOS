# InterviewOS — Product Roadmap

**Product:** AI Voice Interview Coach  
**Version:** v1.0  
**Document Type:** MVP → v2 → v3 Milestones

---

## 1. Product Vision

InterviewOS is a voice-based AI interview coach that helps software engineering candidates practice realistic interviews.

The platform should simulate a real interviewer by:

```text
Reading candidate resume
Understanding target job description
Asking role-specific questions
Speaking questions using AI voice
Recording spoken answers
Transcribing answers
Evaluating performance
Generating a detailed scorecard
Tracking improvement over time
```

---

# 2. Product Positioning

## One-line Pitch

```text
InterviewOS is an AI-powered voice interview coach for software engineering candidates.
```

## Longer Pitch

```text
InterviewOS helps candidates practice realistic software engineering interviews through voice-based AI conversations, resume-aware questions, answer evaluation, and detailed performance scorecards.
```

## Target Users

```text
Software Engineer candidates
SDET candidates
Backend Engineer candidates
Students and fresh graduates
Career switchers entering software roles
International job seekers preparing for interviews
```

---

# 3. Roadmap Overview

```text
MVP: Core interview loop
v2: Better intelligence + better UX
v3: Real-time voice platform + monetization
```

---

# 4. MVP — Version 1.0

## 4.1 Goal

Build a working full-stack AI voice interview platform.

The MVP should prove:

```text
Can the user upload resume/JD?
Can AI generate good interview questions?
Can the AI interviewer speak?
Can the user answer by microphone?
Can the system transcribe and evaluate the answer?
Can the user receive a useful scorecard?
```

---

## 4.2 MVP Core Features

### Authentication

```text
User signup/login
JWT-based backend auth
User-specific sessions
```

### Resume Upload

```text
PDF upload
File validation
Resume text extraction
LLM-based structured parsing
Store parsed profile
```

### Job Description Input

```text
Paste JD text
Extract key skills and responsibilities
Use JD in question generation
```

### Interview Setup

```text
No-resume quick-start interview
Resume-based interview
JD-based interview
Resume + JD interview
```



```text
Select interview type:
- SDE
- SDET
- Backend
- Behavioral
- Resume-based
- JD-based

Select difficulty:
- Easy
- Medium
- Hard

Select question count:
- Free MVP max: 5
```

### Question Generation

```text
Generate first question
Generate next question
Generate follow-up question
Avoid repeated questions
Use resume and JD context
```

### Voice Interviewer

```text
Use fixed ElevenLabs interviewer voice
Generate audio for each question
Frontend audio playback
Text fallback if voice fails
```

### Answer Recording

```text
Browser microphone recording
MediaRecorder API
Audio upload to backend
60-second answer limit
```

### Transcription

```text
Whisper / STT integration
Return transcript
Delete raw audio after transcription
```

### Answer Evaluation

```text
Technical correctness score
Clarity score
Depth score
Confidence score
Relevance score
Communication score
Overall score
Strengths and improvements
```

### Final Scorecard

```text
Overall score
Score breakdown
Question-by-question review
Strengths
Weaknesses
Recommended topics
Final advice
```

### Dashboard

```text
Interview history
Past scorecards
Session status
Basic usage limits
```

---

## 4.3 MVP APIs

```text
GET  /api/health
GET  /api/me
POST /api/resume/upload
GET  /api/resume/latest
POST /api/interview/start
POST /api/interview/question
POST /api/audio/transcribe
POST /api/interview/evaluate
POST /api/interview/final-report
GET  /api/interview/history
GET  /api/interview/{session_id}/scorecard
GET  /api/usage
```

---

## 4.4 MVP Tech Stack

```text
Frontend: Next.js + React + Tailwind CSS
Backend: FastAPI + Python
Database: Supabase PostgreSQL
Auth: Supabase Auth
Storage: Supabase Storage / S3 / Cloudflare R2
LLM: OpenAI / Claude
STT: Whisper
TTS: ElevenLabs
Deployment: Vercel + Render/Railway
```

---

## 4.5 MVP Success Criteria

MVP is successful if:

```text
A user can complete a 5-question voice interview
Each question is relevant to resume or JD
Each answer is transcribed correctly enough
Each answer receives useful feedback
Final scorecard feels valuable
Average session does not break due to latency
Costs are controlled by rate limits
```

---

# 5. MVP Build Milestones

## Milestone 1 — Project Setup

```text
Create monorepo
Setup frontend
Setup backend
Setup environment variables
Setup Supabase project
Create health check API
Deploy basic frontend and backend
```

## Milestone 2 — Resume Upload

```text
Build resume upload UI
Add PDF validation
Create /api/resume/upload
Extract text from PDF
Create resume parser service
Store parsed resume
```

## Milestone 3 — Interview Session

```text
Create session database tables
Create /api/interview/start
Add interview setup UI
Store interview type, difficulty, JD, target role
```

## Milestone 4 — Question Generation

```text
Create prompt files
Create LLM service
Create /api/interview/question
Generate first question
Store question in DB
Return question to frontend
```

## Milestone 5 — Voice Output

```text
Create ElevenLabs voice service
Generate question audio
Return audio_url
Add frontend audio player
Add TTS caching
```

## Milestone 6 — Answer Recording

```text
Create MicRecorder component
Record audio/webm
Validate duration
Upload audio to backend
Create /api/audio/transcribe
Return transcript
```

## Milestone 7 — Answer Evaluation

```text
Create evaluation prompt
Create /api/interview/evaluate
Generate scores and feedback
Store answer and score
Show feedback in frontend
```

## Milestone 8 — Interview Loop

```text
Connect question → answer → evaluation → next question
Add progress states
Handle errors and retries
Limit max questions
```

## Milestone 9 — Final Scorecard

```text
Create /api/interview/final-report
Create scorecard UI
Show final report
Add question-by-question reviews
```

## Milestone 10 — Dashboard + Polish

```text
Interview history
Usage limits
Delete session
Responsive UI
README
Demo video
Deployment
```

---

# 6. Version 2 — Better Intelligence + Better UX

## 6.1 Goal

Make InterviewOS feel smarter, faster, and more personalized.

---

## 6.2 v2 Features

### Better Prompting

```text
Prompt versioning
Prompt quality tests
Company-specific prompts
Role-specific evaluation rubrics
```

### Latency Improvements

```text
SSE progress events
Streaming LLM text
Partial feedback loading
Faster model routing
Optimized audio upload
```

### Advanced Interview Modes

```text
System design interview
DSA explanation interview
SDET automation round
Backend API design round
Behavioral STAR round
```

### Voice Confidence Analysis

```text
Filler word detection
Speaking pace
Long pauses
Answer length
Confidence estimate
```

### Better Dashboard

```text
Progress over time
Score trends
Weak topic tracking
Recommended practice plan
```

### Shareable Reports

```text
Public/private scorecard link
PDF export
LinkedIn-friendly summary
```

---

## 6.3 v2 APIs

```text
POST /api/interview/turn
POST /api/interview/turn/stream
GET  /api/analytics/progress
GET  /api/recommendations/topics
POST /api/report/export/pdf
POST /api/report/share
```

---

## 6.4 v2 Success Criteria

v2 is successful if:

```text
Question quality feels close to a real interviewer
First visible response appears under 500 ms
First spoken follow-up starts under 3 seconds
Users can track improvement across sessions
Reports are good enough to share
```

---

# 7. Version 3 — Real-Time Voice Platform

## 7.1 Goal

Turn InterviewOS from a mock interview app into a real-time AI voice coaching platform.

---

## 7.2 v3 Features

### Real-Time Voice Interview

```text
Streaming STT
Streaming LLM
Chunked TTS
Low-latency audio playback
Interruptions / barge-in
Natural conversation flow
```

### Company-Specific Interview Packs

```text
Amazon SDE style
Google software engineering style
Meta behavioral + product sense
Startup backend engineer style
SDET automation specialist style
```

### Paid Plans

```text
Free plan
Pro plan
Bootcamp plan
College plan
Team plan
```

### White-Label Platform

```text
Bootcamps can create branded interview practice rooms
Companies can create internal candidate prep tools
Universities can use it for placement training
```

### Admin Console

```text
User management
Interview templates
Prompt tuning
Usage analytics
Cost monitoring
Report exports
```

### Developer API

```text
Create interview session
Submit answer audio
Fetch scorecard
Embed interview widget
```

---

## 7.3 v3 APIs

```text
POST /api/realtime/session/start
WS   /api/realtime/interview
POST /api/templates
GET  /api/templates
POST /api/company-packs
POST /api/billing/checkout
GET  /api/admin/usage
GET  /api/admin/costs
POST /api/developer/sessions
```

---

## 7.4 v3 Success Criteria

v3 is successful if:

```text
Voice conversation feels natural
Paid users complete multiple sessions
Bootcamps or teams show interest
Cost per session is predictable
The system supports white-label use cases
```

---

# 8. Monetization Roadmap

## 8.1 Free Plan

```text
1 full interview after signup
5 questions
Basic scorecard
Limited history
```

## 8.2 Pro Plan

```text
Unlimited or monthly quota interviews
Advanced scorecards
Company-specific interview modes
Progress tracking
PDF export
Longer answers
```

## 8.3 Bootcamp / College Plan

```text
Bulk student accounts
Admin dashboard
Progress analytics
Placement preparation reports
Custom interview templates
```

## 8.4 B2B API

```text
API access for hiring platforms
Embedded interview coach
White-label voice interview practice
```

---

# 9. Portfolio Roadmap

If the goal is job search, prioritize this order:

```text
1. Strong GitHub README
2. Clean architecture docs
3. Working deployed demo
4. 2-minute demo video
5. Resume bullet points
6. LinkedIn project post
7. System design explanation
```

---

# 10. Resume Bullet

Use this after MVP:

```text
Built InterviewOS, an AI-powered voice interview coach using Next.js, FastAPI, OpenAI, Whisper, and ElevenLabs. Implemented resume-aware question generation, browser microphone recording, speech-to-text transcription, LLM-based answer evaluation, and detailed performance scorecards.
```

Stronger version after v2:

```text
Built a production-style AI voice interview platform with resume-aware prompting, STT → LLM → TTS pipeline, latency-aware UX states, rate-limited API design, TTS caching, and structured interview analytics.
```

---

# 11. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Generic LLM questions | Strong prompt design and prompt tests |
| High latency | UX states, caching, streaming in v2 |
| High AI cost | Rate limits, model routing, TTS cache |
| Bad transcription | Retry flow, manual answer fallback |
| Weak final reports | Strong report prompt and scoring rubric |
| Voice API failure | Text fallback |
| Resume parsing errors | Show editable parsed profile later |
| User privacy concerns | Delete raw audio, private storage, data deletion |

---

# 12. Final Roadmap Summary

## MVP

```text
Build the core voice interview loop.
```

## v2

```text
Improve intelligence, speed, and analytics.
```

## v3

```text
Become a real-time voice interview coaching platform with monetization.
```

The immediate goal is not to build every feature.

The immediate goal is:

```text
A polished 5-question AI voice interview that feels real and produces a useful scorecard.
```
