# InterviewOS — Cost Control

**Product:** AI Voice Interview Coach  
**Version:** v1.0 MVP  
**Document Type:** Rate Limits + Free Tier Rules + AI Cost Strategy

---

## 1. Why Cost Control Matters

InterviewOS uses multiple paid AI services:

```text
Speech-to-text
LLM question generation
LLM answer evaluation
LLM final scorecard
ElevenLabs text-to-speech
File storage
Database
```

A single interview session may include:

```text
5–10 questions
5–10 audio transcriptions
5–10 answer evaluations
5–10 TTS generations
1 final report generation
```

Without limits, even a small number of users can create high costs.

Cost control must be built from day one.

---

# 2. Cost Drivers

## 2.1 Main Cost Sources

| Service | Used For | Cost Risk |
|---|---|---|
| STT / Whisper | Transcribing candidate answers | Long audio answers |
| LLM | Question generation and evaluation | Long resumes, long answers, high token use |
| ElevenLabs | Interviewer voice audio | Repeated TTS calls |
| Storage | Resume PDFs and temporary audio | Large files and retention |
| Database | Sessions, answers, scores | Low cost but grows with history |

---

# 3. Free Tier Rules

## 3.1 Anonymous User

Anonymous usage should be very limited.

```text
No full interview
Only product demo
1 sample question
No resume storage
No interview history
```

## 3.2 Free Registered User

```text
1 full free interview after signup
5 questions in the free interview
60 seconds maximum per answer
10MB maximum audio upload
10MB maximum resume upload
1 active resume stored
30-minute session timeout
```

After the one free interview is used:

```text
User must upgrade or receive manually granted demo credits.
```

## 3.3 Pro User — Future

```text
Unlimited or higher monthly interview quota
10–20 questions per interview
Longer answer duration
Advanced reports
Company-specific interview modes
Progress analytics
Shareable scorecards
```

---

## 3.4 Final Free Tier Decision

Use this single rule everywhere in product copy, backend checks, and docs:

```text
Free user = 1 full interview after signup.
```

Do not advertise "3 interviews per day" in the public MVP. That can exist only as a development/demo environment variable for testing.

---

# 4. Rate Limits

## 4.1 API Rate Limits

| Endpoint | Free Limit | Notes |
|---|---:|---|
| `POST /api/resume/upload` | 3/day | Prevent repeated expensive parsing |
| `POST /api/interview/start` | 1 free interview total | Signup free interview limit |
| `POST /api/interview/question` | 5/session | MVP free tier |
| `POST /api/audio/transcribe` | 5/session | One answer per question |
| `POST /api/interview/evaluate` | 5/session | One evaluation per answer |
| `POST /api/interview/final-report` | 1/session | Only after completion |
| `GET /api/interview/history` | 60/hour | Dashboard protection |
| `GET /api/usage` | 60/hour | Low-cost endpoint |

---

# 5. Session Limits

## 5.1 MVP Free Session

```text
Max questions: 5
Max answer duration: 60 seconds
Max session duration: 30 minutes
Max retries per question: 2
Max final report generations: 1
```

## 5.2 Abuse Prevention

Block or slow down:

```text
Repeated failed uploads
Repeated transcription retries
Multiple sessions started but not completed
Very long text inputs
Same user creating many accounts
```

---

# 6. File Limits

## 6.1 Resume Upload

```text
Allowed type: PDF only
Max file size: 10MB
Max pages: 5 pages for free users
Storage: private bucket
Retention: until user deletes or account is deleted
```

## 6.2 Audio Upload

```text
Allowed types: audio/webm, audio/mp3, audio/wav
Recommended frontend type: audio/webm
Max file size: 10MB
Max duration: 60 seconds
Retention: delete immediately after transcription
```

---

# 7. Token Limits

## 7.1 Resume Parsing

```text
Max resume text tokens: 6000
If longer: summarize sections first
Model: GPT-4o-mini for MVP
```

## 7.2 Question Generation

```text
Max input tokens: 4000
Max output tokens: 400
Model: GPT-4o-mini or stronger model for quality
```

## 7.3 Answer Evaluation

```text
Max answer transcript tokens: 1200
Max output tokens: 800
Model: GPT-4o-mini
```

## 7.4 Final Report

```text
Max input tokens: 8000
Max output tokens: 1500
Model: GPT-4o / Claude Sonnet / strong model
```

---

# 8. Model Routing Strategy

## 8.1 Use Cheaper Model For

```text
Resume extraction
Basic question generation
Per-answer evaluation
Topic recommendations
Short summaries
```

Recommended:

```text
GPT-4o-mini
```

## 8.2 Use Stronger Model For

```text
Final report
Complex resume-aware interview plan
System design interview mode
High-quality paid-user evaluation
```

Recommended:

```text
GPT-4o / Claude Sonnet equivalent
```

---

# 9. ElevenLabs Cost Control

## 9.1 Use One Fixed Interviewer Voice

For MVP:

```text
No user voice cloning
No custom voice marketplace
One fixed interviewer voice
```

This avoids:

```text
Voice cloning abuse
Consent risk
Unnecessary API usage
Storage complexity
```

## 9.2 TTS Caching

Cache generated audio.

Cache key:

```text
hash(question_text + voice_id + voice_settings)
```

If the same question appears again:

```text
Return cached audio_url
Do not call ElevenLabs again
```

## 9.3 Voice Generation Limits

```text
Max TTS calls per session: equal to max questions
Retry limit: 1
Fallback: show text question if voice fails
```

---

# 10. STT Cost Control

## 10.1 Audio Duration Limit

```text
Free user: 60 seconds
Pro user future: 180 seconds
```

## 10.2 Silence Detection

Before upload or before transcription:

```text
Detect empty/silent audio
Reject very low-volume recordings
Ask user to re-record
```

## 10.3 Optional Manual Text Fallback

If transcription fails, allow:

```text
Type your answer manually
```

This avoids repeated STT cost.

---

# 11. Storage Cost Control

## 11.1 Raw Audio

```text
Delete immediately after transcription
Do not store by default
Store only transcript and metadata
```

## 11.2 Generated Question Audio

```text
Store cached TTS audio
Apply expiry policy if not reused
Delete old audio after 30 days for free users
```

## 11.3 Resumes

```text
Free users: 1 active resume
Pro users future: multiple resumes
Allow user deletion
```

---

# 12. Usage Tracking

Create a `usage_events` table.

## 12.1 Suggested Columns

```text
id
user_id
event_type
session_id
resource_id
model_name
input_tokens
output_tokens
audio_duration_seconds
estimated_cost_usd
created_at
```

## 12.2 Event Types

```text
resume_parse
question_generation
tts_generation
audio_transcription
answer_evaluation
final_report
```

---

# 13. Cost Estimation Per Session

## 13.1 MVP Free Interview

Assume:

```text
5 questions
5 transcriptions
5 evaluations
5 TTS generations
1 final report
```

Estimated cost range:

```text
$0.20 – $0.80 per full session
```

Actual cost depends on provider pricing, model selection, audio duration, and token usage.

---

# 14. Daily Cost Guardrail

Set application-level daily cost caps.

## Example

```text
Daily AI budget cap: $20 during development/demo
If cap reached:
    Disable new demo/free-credit interviews
    Allow viewing past reports
    Show friendly message
```

Message:

```text
Free interview capacity is full for today. Please try again tomorrow.
```

---

# 15. Backend Enforcement

Cost controls should be enforced in backend, not only frontend.

## Required Middleware / Services

```text
auth_middleware
rate_limit_middleware
usage_service
plan_service
quota_service
cost_logger
```

## Before expensive call, check:

```text
Is user authenticated?
Is session active?
Is quota available?
Is file size valid?
Is duration valid?
Is daily budget available?
```

---

# 16. Rate Limit Headers

Return headers from API:

```http
X-RateLimit-Limit: 1
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2026-04-30T23:59:59Z
```

For session-level limits:

```http
X-Session-Question-Limit: 5
X-Session-Questions-Remaining: 3
```

---

# 17. User-Facing Free Tier Copy

Use clear copy:

```text
Free plan includes:
- 1 complete AI voice interview after signup
- 5 interview questions
- 60 seconds per answer
- Basic scorecard
```

Upgrade copy later:

```text
Upgrade for longer interviews, advanced reports, company-specific practice, and progress tracking.
```

---

# 18. Developer Mode Limits

During local development:

```text
Disable real TTS by default
Use mock transcription for tests
Use fake LLM responses for UI testing
Add USE_MOCK_AI=true env variable
```

This prevents accidental costs while coding.

---

# 19. Environment Variables

```env
USE_MOCK_AI=false
DAILY_AI_BUDGET_USD=20
FREE_INTERVIEW_TOTAL_LIMIT=1
FREE_SESSION_QUESTION_LIMIT=5
FREE_MAX_AUDIO_SECONDS=60
FREE_MAX_AUDIO_MB=10
FREE_MAX_RESUME_MB=10
TTS_CACHE_ENABLED=true
RAW_AUDIO_RETENTION=false
```

---

# 20. Cost Control MVP Checklist

Before public demo, implement:

```text
JWT authentication
Signup free interview limit
Session question limit
Audio duration validation
Audio file size validation
Resume file size validation
Raw audio deletion
TTS caching
Model routing
Usage logging
Friendly quota error messages
```

---

# 21. Final Rule

Every expensive operation must answer this before running:

```text
Is this request allowed, necessary, and within quota?
```

If not, reject early with a clear error.
