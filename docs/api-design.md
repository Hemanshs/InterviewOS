# InterviewOS — API Design

**Product:** AI Voice Interview Coach  
**Version:** v1.0 MVP  
**API Style:** REST  
**Backend:** FastAPI  
**Base URL:** `/api`

---

## 1. API Design Goals

The API should support the full InterviewOS flow:

```text
Resume upload
   ↓
Interview session creation
   ↓
Question generation
   ↓
Voice generation
   ↓
User audio transcription
   ↓
Answer evaluation
   ↓
Next question / follow-up
   ↓
Final scorecard
   ↓
Interview history dashboard
```

The design prioritizes:

- Clear REST endpoints
- Strong request/response schemas
- JWT-based authentication
- Audio upload support
- Resume and job description context
- Cost control and rate limiting
- Production-style error handling
- Easy frontend integration with Next.js

---

## 2. Authentication

All protected routes require a JWT access token.

### Header

```http
Authorization: Bearer <access_token>
```

### Auth Provider

MVP recommendation:

```text
Supabase Auth
```

The frontend handles login/signup and sends the JWT to the FastAPI backend.

---

## 3. Common Response Format

### Success Response

```json
{
  "success": true,
  "data": {},
  "message": "Request completed successfully"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload",
    "details": {}
  }
}
```

---

## 4. Common Error Codes

| Code | Meaning |
|---|---|
| `UNAUTHORIZED` | Missing or invalid token |
| `FORBIDDEN` | User does not have access |
| `VALIDATION_ERROR` | Invalid input payload |
| `FILE_TOO_LARGE` | Uploaded file exceeds size limit |
| `UNSUPPORTED_FILE_TYPE` | Invalid file type |
| `RATE_LIMIT_EXCEEDED` | User exceeded daily/session limit |
| `SESSION_NOT_FOUND` | Interview session does not exist |
| `SESSION_ALREADY_COMPLETED` | Cannot modify completed session |
| `QUESTION_NOT_FOUND` | Question does not exist |
| `TRANSCRIPTION_FAILED` | STT provider failed |
| `LLM_FAILED` | LLM provider failed |
| `VOICE_GENERATION_FAILED` | ElevenLabs failed |
| `INTERNAL_ERROR` | Unknown backend error |

---

## 5. Rate Limit Rules

### Free tier product rule

The MVP product rule is:

```text
Each registered free user gets 1 full free interview after signup.
```

That free interview includes:

```text
5 questions
60 seconds per answer
1 resume stored
Basic scorecard
```

Development/demo environments may use configurable daily credits, but the public free-tier rule should remain one full free interview per registered user.


### Free User

```text
1 free interview total
Max 5 questions per interview
Max 60 seconds audio per answer
Max 10MB audio upload
Max 1 resume stored at a time
```

### Logged-in Free User

```text
1 free interview after signup
Max 10 questions per session
Session timeout after 30 minutes inactivity
```

### Headers

The backend should return rate limit headers:

```http
X-RateLimit-Limit: 1
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2026-04-30T23:59:59Z
```

---

# 6. Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/me` | Get current user profile |
| `DELETE` | `/api/account` | Delete account and all user data |
| `POST` | `/api/resume/upload` | Upload and parse resume |
| `GET` | `/api/resume/latest` | Fetch latest parsed resume |
| `DELETE` | `/api/resume/{resume_id}` | Delete resume |
| `POST` | `/api/interview/start` | Start interview session |
| `POST` | `/api/interview/question` | Generate next question + voice |
| `POST` | `/api/audio/transcribe` | Transcribe user audio |
| `POST` | `/api/interview/evaluate` | Evaluate answer |
| `POST` | `/api/interview/final-report` | Generate final report |
| `GET` | `/api/interview/history` | Fetch interview history |
| `GET` | `/api/interview/{session_id}` | Fetch session details |
| `GET` | `/api/interview/{session_id}/scorecard` | Fetch full scorecard |
| `POST` | `/api/interview/{session_id}/complete` | Manually complete session |
| `DELETE` | `/api/interview/{session_id}` | Delete interview session |
| `GET` | `/api/usage` | Fetch usage/cost-limit status |

---

# 7. System / User APIs

---

## 7.1 Health Check

```http
GET /api/health
```

### Auth

Not required.

### Response

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "service": "interviewos-api",
    "version": "1.0.0",
    "timestamp": "2026-04-30T08:00:00Z"
  }
}
```

---

## 7.2 Get Current User

```http
GET /api/me
```

### Auth

Required.

### Response

```json
{
  "success": true,
  "data": {
    "id": "user_8f4a9a1b",
    "email": "candidate@example.com",
    "plan": "free",
    "created_at": "2026-04-30T08:00:00Z",
    "usage": {
      "free_interview_used": true,
      "free_interviews_total": 1,
      "remaining_free_interviews": 0
    }
  }
}
```

---


---

## 7.3 Delete Account

```http
DELETE /api/account
```

Deletes the authenticated user's account data.

### Auth

Required.

### Purpose

This endpoint implements the user data deletion requirement.

It should delete or soft-delete:

```text
User profile
Resumes
Interview sessions
Questions
Answers
Scores
Reports
Usage events
Stored files owned by the user
Generated audio owned by the user
```

Raw answer audio should already be deleted after transcription, but this endpoint should also remove any remaining user-scoped files.

### Request Body

```json
{
  "confirmation": "DELETE_MY_ACCOUNT"
}
```

### Success Response

```json
{
  "success": true,
  "data": {
    "user_id": "user_8f4a9a1b",
    "deleted": true,
    "deleted_at": "2026-04-30T09:00:00Z"
  },
  "message": "Account and user data deleted successfully"
}
```

### Invalid Confirmation Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Account deletion requires confirmation text",
    "details": {
      "required_confirmation": "DELETE_MY_ACCOUNT"
    }
  }
}
```


# 8. Resume APIs

---

## 8.1 Upload Resume

```http
POST /api/resume/upload
```

Uploads a resume PDF, stores it, parses it, and extracts structured candidate profile data.

### Auth

Required.

### Content Type

```http
multipart/form-data
```

### Request Fields

| Field | Type | Required | Description |
|---|---:|---:|---|
| `file` | File | Yes | Resume PDF |
| `parse_with_llm` | Boolean | No | Whether to use LLM-based structured parsing |
| `replace_existing` | Boolean | No | Replace existing resume for free users |

### Example Request

```bash
curl -X POST "https://api.example.com/api/resume/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf" \
  -F "parse_with_llm=true" \
  -F "replace_existing=true"
```

### Success Response

```json
{
  "success": true,
  "data": {
    "resume_id": "res_7b21c9",
    "file_name": "resume.pdf",
    "file_url": "private://resumes/user_8f4a9a1b/resume.pdf",
    "parsed": true,
    "profile": {
      "candidate_name": "Rahul Sharma",
      "email": "rahul@example.com",
      "phone": "+91-9000000000",
      "location": "India",
      "summary": "Software engineer with experience in backend APIs and test automation.",
      "skills": [
        "Python",
        "FastAPI",
        "React",
        "Playwright",
        "PostgreSQL",
        "Docker"
      ],
      "experience": [
        {
          "company": "Eltropy",
          "role": "SDET",
          "start_date": "2023-08",
          "end_date": "2025-06",
          "highlights": [
            "Built automation suites using Playwright",
            "Improved CI pipeline stability"
          ]
        }
      ],
      "projects": [
        {
          "name": "AI Resume Matcher",
          "description": "Built a resume-job matching tool using FastAPI and LLMs.",
          "technologies": ["FastAPI", "OpenAI", "PostgreSQL"]
        }
      ],
      "education": [
        {
          "institution": "BITS Pilani Goa",
          "degree": "B.Tech Chemical Engineering",
          "start_year": 2019,
          "end_year": 2023
        }
      ]
    },
    "created_at": "2026-04-30T08:00:00Z"
  },
  "message": "Resume uploaded and parsed successfully"
}
```

### Error Responses

#### File Too Large

```json
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "Resume file must be less than 10MB",
    "details": {
      "max_size_mb": 10
    }
  }
}
```

#### Unsupported File

```json
{
  "success": false,
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "Only PDF resumes are supported in MVP",
    "details": {
      "allowed_types": ["application/pdf"]
    }
  }
}
```

---

## 8.2 Get Latest Resume

```http
GET /api/resume/latest
```

### Auth

Required.

### Response

```json
{
  "success": true,
  "data": {
    "resume_id": "res_7b21c9",
    "file_name": "resume.pdf",
    "parsed": true,
    "profile": {
      "candidate_name": "Rahul Sharma",
      "skills": ["Python", "FastAPI", "React", "Playwright"],
      "experience_years": 2,
      "latest_role": "SDET"
    },
    "created_at": "2026-04-30T08:00:00Z"
  }
}
```

---

## 8.3 Delete Resume

```http
DELETE /api/resume/{resume_id}
```

### Auth

Required.

### Response

```json
{
  "success": true,
  "data": {
    "resume_id": "res_7b21c9",
    "deleted": true
  },
  "message": "Resume deleted successfully"
}
```

---

# 9. Interview APIs

---

## 9.1 Start Interview Session

```http
POST /api/interview/start
```

Creates a new interview session using resume, job description, and selected interview type.

### Auth

Required.

### Request Body

```json
{
  "resume_id": "res_7b21c9",
  "interview_type": "sde",
  "difficulty": "medium",
  "job_description": "We are hiring a backend engineer with experience in Python, FastAPI, PostgreSQL, Docker, and cloud deployments.",
  "target_company": "Amazon",
  "target_role": "Software Development Engineer",
  "question_count": 5,
  "voice_enabled": true
}
```

### Field Details

| Field | Type | Required | Allowed Values / Notes |
|---|---:|---:|---|
| `resume_id` | String | No | Required for resume-based interviews |
| `interview_type` | String | Yes | `sde`, `sdet`, `backend`, `behavioral`, `system_design`, `resume_based`, `jd_based` |
| `difficulty` | String | No | `easy`, `medium`, `hard` |
| `job_description` | String | No | Plain text JD |
| `target_company` | String | No | Example: Amazon, Google, Meta |
| `target_role` | String | No | Example: Backend Engineer |
| `question_count` | Integer | No | Free limit: max 5 |
| `voice_enabled` | Boolean | No | Generate TTS for questions |

### Success Response

```json
{
  "success": true,
  "data": {
    "session_id": "ses_91a2bf",
    "status": "in_progress",
    "interview_type": "sde",
    "difficulty": "medium",
    "question_count": 5,
    "started_at": "2026-04-30T08:10:00Z",
    "limits": {
      "max_questions": 5,
      "max_answer_duration_seconds": 60
    },
    "next_action": {
      "type": "generate_question",
      "endpoint": "/api/interview/question"
    }
  },
  "message": "Interview session started"
}
```

### Rate Limit Error

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You have reached your daily interview limit",
    "details": {
      "free_interviews_total": 1,
      "free_interview_used": true,
      "reset_at": "2026-04-30T23:59:59Z"
    }
  }
}
```

---

## 9.2 Generate Next Question

```http
POST /api/interview/question
```

Generates the next question, optionally creates interviewer voice audio, and stores the question.

### Auth

Required.

### Request Body

```json
{
  "session_id": "ses_91a2bf",
  "mode": "next",
  "previous_answer_id": "ans_23d1aa",
  "include_voice": true
}
```

### Field Details

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `session_id` | String | Yes | Active interview session |
| `mode` | String | No | `first`, `next`, `follow_up` |
| `previous_answer_id` | String | No | Used for follow-up generation |
| `include_voice` | Boolean | No | If true, generate ElevenLabs audio |

### Success Response

```json
{
  "success": true,
  "data": {
    "session_id": "ses_91a2bf",
    "question": {
      "question_id": "q_812abc",
      "sequence": 1,
      "type": "technical",
      "difficulty": "medium",
      "question_text": "Your resume mentions Playwright automation. How would you handle flaky tests in a CI/CD pipeline?",
      "expected_focus_areas": [
        "Root cause analysis",
        "Retry strategy",
        "Stable selectors",
        "Test isolation",
        "CI observability"
      ],
      "time_limit_seconds": 60,
      "audio": {
        "enabled": true,
        "audio_url": "https://cdn.example.com/audio/q_812abc.mp3",
        "duration_seconds": 9.4,
        "cached": false
      }
    },
    "latency_state": {
      "current": "ready_for_answer",
      "completed_steps": [
        "question_generated",
        "voice_generated"
      ]
    }
  },
  "message": "Question generated successfully"
}
```

### Question Limit Error

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Maximum questions reached for this session",
    "details": {
      "max_questions": 5,
      "current_questions": 5
    }
  }
}
```

---

## 9.3 Get Interview Session

```http
GET /api/interview/{session_id}
```

Fetches full interview session state.

### Auth

Required.

### Response

```json
{
  "success": true,
  "data": {
    "session_id": "ses_91a2bf",
    "status": "in_progress",
    "interview_type": "sde",
    "difficulty": "medium",
    "started_at": "2026-04-30T08:10:00Z",
    "ended_at": null,
    "progress": {
      "current_question": 2,
      "total_questions": 5,
      "percentage": 40
    },
    "questions": [
      {
        "question_id": "q_812abc",
        "sequence": 1,
        "question_text": "Your resume mentions Playwright automation. How would you handle flaky tests in a CI/CD pipeline?",
        "audio_url": "https://cdn.example.com/audio/q_812abc.mp3",
        "answered": true,
        "answer_id": "ans_23d1aa",
        "score_id": "score_77bd21"
      }
    ]
  }
}
```

---

## 9.4 Complete Interview Session

```http
POST /api/interview/{session_id}/complete
```

Marks a session as complete. Usually called before generating final report if the user ends early.

### Auth

Required.

### Request Body

```json
{
  "reason": "user_finished"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "session_id": "ses_91a2bf",
    "status": "completed",
    "ended_at": "2026-04-30T08:40:00Z"
  },
  "message": "Interview completed"
}
```

---

## 9.5 Delete Interview Session

```http
DELETE /api/interview/{session_id}
```

Deletes session data, including questions, answers, scores, and generated audio references.

### Auth

Required.

### Response

```json
{
  "success": true,
  "data": {
    "session_id": "ses_91a2bf",
    "deleted": true
  },
  "message": "Interview session deleted"
}
```

---

# 10. Audio APIs

---

## 10.1 Transcribe User Audio

```http
POST /api/audio/transcribe
```

Uploads the candidate's recorded answer audio and returns transcript text.

### Auth

Required.

### Content Type

```http
multipart/form-data
```

### Request Fields

| Field | Type | Required | Description |
|---|---:|---:|---|
| `session_id` | String | Yes | Active interview session |
| `question_id` | String | Yes | Question being answered |
| `audio_file` | File | Yes | Recorded audio blob |
| `duration_seconds` | Number | Yes | Audio duration |
| `language` | String | No | Default: `en` |

### Example Request

```bash
curl -X POST "https://api.example.com/api/audio/transcribe" \
  -H "Authorization: Bearer <token>" \
  -F "session_id=ses_91a2bf" \
  -F "question_id=q_812abc" \
  -F "duration_seconds=42" \
  -F "language=en" \
  -F "audio_file=@answer.webm"
```

### Success Response

```json
{
  "success": true,
  "data": {
    "answer_id": "ans_23d1aa",
    "session_id": "ses_91a2bf",
    "question_id": "q_812abc",
    "transcript": "I would first identify whether the flakiness is caused by timing issues, unstable selectors, shared state, or external dependencies...",
    "language": "en",
    "duration_seconds": 42,
    "word_count": 96,
    "filler_words": {
      "count": 5,
      "examples": ["um", "like", "you know"]
    },
    "raw_audio_deleted": true,
    "submitted_at": "2026-04-30T08:18:00Z",
    "latency": {
      "transcription_ms": 1430
    }
  },
  "message": "Audio transcribed successfully"
}
```

### Duration Limit Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Audio duration exceeds the allowed limit",
    "details": {
      "max_duration_seconds": 60,
      "received_duration_seconds": 95
    }
  }
}
```

---

# 11. Evaluation APIs

---

## 11.1 Evaluate Answer

```http
POST /api/interview/evaluate
```

Evaluates a candidate answer against the interview question.

### Auth

Required.

### Request Body

```json
{
  "session_id": "ses_91a2bf",
  "question_id": "q_812abc",
  "answer_id": "ans_23d1aa",
  "generate_follow_up": true
}
```

### Success Response

```json
{
  "success": true,
  "data": {
    "score_id": "score_77bd21",
    "session_id": "ses_91a2bf",
    "question_id": "q_812abc",
    "answer_id": "ans_23d1aa",
    "scores": {
      "technical_correctness": 8,
      "clarity": 7,
      "depth": 8,
      "confidence": 7,
      "relevance": 9,
      "structure": 7,
      "communication": 7,
      "conciseness": 6,
      "example_quality": 8,
      "overall": 7.5
    },
    "feedback": {
      "summary": "Strong answer with good coverage of flaky test causes and mitigation strategies.",
      "strengths": [
        "Mentioned root cause analysis",
        "Covered stable selectors and retries",
        "Connected the answer to CI/CD reliability"
      ],
      "improvements": [
        "Could mention test isolation more clearly",
        "Could include an example from a real project",
        "Answer was slightly long"
      ],
      "ideal_answer_points": [
        "Classify flaky tests by root cause",
        "Avoid blind retries",
        "Use deterministic waits instead of sleep",
        "Improve selectors and test data isolation",
        "Track flaky test metrics in CI"
      ]
    },
    "follow_up": {
      "recommended": true,
      "question_text": "Can you give one real example of a flaky test you fixed and explain what the root cause was?"
    },
    "latency": {
      "evaluation_ms": 1880
    }
  },
  "message": "Answer evaluated successfully"
}
```

---

# 12. Final Report APIs

---

## 12.1 Generate Final Report

```http
POST /api/interview/final-report
```

Generates and stores the final scorecard for a completed or ended interview session.

### Auth

Required.

### Request Body

```json
{
  "session_id": "ses_91a2bf",
  "include_transcript": true,
  "include_recommendations": true
}
```

### Success Response

```json
{
  "success": true,
  "data": {
    "report_id": "rep_45cbb2",
    "session_id": "ses_91a2bf",
    "status": "completed",
    "overall_score": 7.6,
    "score_breakdown": {
      "technical": 7.8,
      "communication": 7.2,
      "confidence": 7.0,
      "problem_solving": 8.0,
      "role_fit": 7.9
    },
    "summary": "The candidate performed well in technical reasoning and showed strong backend/API understanding. Communication was clear, but answers can be more structured and concise.",
    "strengths": [
      "Good understanding of automation reliability",
      "Strong backend API awareness",
      "Able to reason about CI/CD trade-offs"
    ],
    "weaknesses": [
      "Needs more structured STAR-style answers",
      "Should provide more concrete project examples",
      "Could improve conciseness"
    ],
    "recommended_topics": [
      "System design basics",
      "CI/CD observability",
      "Database indexing",
      "Behavioral STAR method"
    ],
    "question_reviews": [
      {
        "question_id": "q_812abc",
        "sequence": 1,
        "question_text": "Your resume mentions Playwright automation. How would you handle flaky tests in a CI/CD pipeline?",
        "answer_id": "ans_23d1aa",
        "overall_score": 7.5,
        "feedback_summary": "Strong answer with good coverage of flaky test causes."
      }
    ],
    "transcript": [
      {
        "question": "Your resume mentions Playwright automation. How would you handle flaky tests in a CI/CD pipeline?",
        "answer": "I would first identify whether the flakiness is caused by timing issues..."
      }
    ],
    "created_at": "2026-04-30T08:45:00Z"
  },
  "message": "Final report generated successfully"
}
```

---

## 12.2 Fetch Scorecard

```http
GET /api/interview/{session_id}/scorecard
```

### Auth

Required.

### Response

```json
{
  "success": true,
  "data": {
    "report_id": "rep_45cbb2",
    "session_id": "ses_91a2bf",
    "overall_score": 7.6,
    "score_breakdown": {
      "technical": 7.8,
      "communication": 7.2,
      "confidence": 7.0,
      "problem_solving": 8.0,
      "role_fit": 7.9
    },
    "summary": "The candidate performed well in technical reasoning and showed strong backend/API understanding.",
    "strengths": [
      "Good understanding of automation reliability",
      "Strong backend API awareness"
    ],
    "weaknesses": [
      "Needs more structured answers",
      "Should provide more concrete examples"
    ],
    "recommended_topics": [
      "System design basics",
      "Database indexing",
      "Behavioral STAR method"
    ],
    "created_at": "2026-04-30T08:45:00Z"
  }
}
```

---

# 13. History / Dashboard APIs

---

## 13.1 Get Interview History

```http
GET /api/interview/history
```

### Auth

Required.

### Query Parameters

| Parameter | Type | Required | Description |
|---|---:|---:|---|
| `page` | Integer | No | Default: 1 |
| `limit` | Integer | No | Default: 10 |
| `status` | String | No | `in_progress`, `completed` |
| `interview_type` | String | No | Filter by interview type |

### Example

```http
GET /api/interview/history?page=1&limit=10&status=completed
```

### Response

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "session_id": "ses_91a2bf",
        "interview_type": "sde",
        "target_role": "Software Development Engineer",
        "target_company": "Amazon",
        "status": "completed",
        "question_count": 5,
        "overall_score": 7.6,
        "started_at": "2026-04-30T08:10:00Z",
        "ended_at": "2026-04-30T08:40:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total_items": 24,
      "total_pages": 3
    }
  }
}
```

---

# 14. Usage APIs

---

## 14.1 Get Usage Status

```http
GET /api/usage
```

### Auth

Required.

### Response

```json
{
  "success": true,
  "data": {
    "plan": "free",
    "limits": {
      "free_interviews_total": 1,
      "questions_per_session": 5,
      "answer_duration_seconds": 60,
      "audio_upload_mb": 10,
      "stored_resumes": 1
    },
    "usage": {
      "free_interview_used": true,
      "questions_used_current_session": 2,
      "resumes_stored": 1
    },
    "remaining": {
      "free_interviews": 0,
      "resumes": 0
    },
    "reset_at": "2026-04-30T23:59:59Z"
  }
}
```

---

# 15. Recommended Frontend Flow

## 15.1 Start Interview Flow

```text
1. GET /api/me
2. POST /api/resume/upload
3. POST /api/interview/start
4. POST /api/interview/question
5. Play question audio
```

## 15.2 Answer Flow

```text
1. User records answer in browser
2. POST /api/audio/transcribe
3. POST /api/interview/evaluate
4. POST /api/interview/question
5. Play next question audio
```

## 15.3 Finish Flow

```text
1. POST /api/interview/{session_id}/complete
2. POST /api/interview/final-report
3. GET /api/interview/{session_id}/scorecard
```

---

# 16. Latency State Contract

The frontend should show progressive states while backend tasks run.

### Suggested UI States

```json
{
  "states": [
    "uploading_resume",
    "parsing_resume",
    "generating_question",
    "generating_voice",
    "ready_for_answer",
    "recording_answer",
    "uploading_audio",
    "transcribing_answer",
    "evaluating_answer",
    "preparing_follow_up",
    "generating_report",
    "completed"
  ]
}
```

### Example State Payload

```json
{
  "latency_state": {
    "current": "evaluating_answer",
    "label": "Evaluating your response...",
    "completed_steps": [
      "audio_uploaded",
      "transcription_completed"
    ],
    "estimated_next_step": "preparing_follow_up"
  }
}
```

---

# 17. Database Entity Mapping

| API Resource | Database Table |
|---|---|
| User | `users` |
| Resume | `resumes` |
| Interview Session | `sessions` |
| Question | `questions` |
| Answer | `answers` |
| Score | `scores` |
| Final Report | `reports` |
| Usage | `usage_events` or computed from sessions |

---

# 18. Suggested Pydantic Models

## 18.1 StartInterviewRequest

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal


class StartInterviewRequest(BaseModel):
    resume_id: Optional[str] = None
    interview_type: Literal[
        "sde",
        "sdet",
        "backend",
        "behavioral",
        "system_design",
        "resume_based",
        "jd_based"
    ]
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    job_description: Optional[str] = None
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    question_count: int = Field(default=5, ge=1, le=10)
    voice_enabled: bool = True
```

## 18.2 GenerateQuestionRequest

```python
from pydantic import BaseModel
from typing import Optional, Literal


class GenerateQuestionRequest(BaseModel):
    session_id: str
    mode: Literal["first", "next", "follow_up"] = "next"
    previous_answer_id: Optional[str] = None
    include_voice: bool = True
```

## 18.3 EvaluateAnswerRequest

```python
from pydantic import BaseModel


class EvaluateAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_id: str
    generate_follow_up: bool = True
```

## 18.4 FinalReportRequest

```python
from pydantic import BaseModel


class FinalReportRequest(BaseModel):
    session_id: str
    include_transcript: bool = True
    include_recommendations: bool = True
```

---

# 19. Implementation Notes

## 19.1 Audio Handling

- Browser should record audio using `MediaRecorder`.
- Recommended MVP format: `audio/webm`.
- Backend should validate:
  - MIME type
  - File size
  - Duration
  - Session ownership
  - Question ownership

## 19.2 Raw Audio Deletion

After transcription:

```text
audio uploaded
   ↓
temporary storage
   ↓
Whisper transcription
   ↓
transcript saved
   ↓
raw audio deleted
```

Store only:

```text
answer transcript
duration
word count
filler word count
metadata
```

## 19.3 TTS Caching

To reduce ElevenLabs cost:

```text
Hash question_text + voice_id
If same hash exists:
    return cached audio_url
Else:
    call ElevenLabs
    store generated audio_url
```

## 19.4 LLM Cost Control

Use:

```text
GPT-4o-mini for:
- answer evaluation
- simple follow-ups
- short summaries

GPT-4o / Claude Sonnet for:
- final report
- high-quality resume-aware question generation
```

---

# 20. MVP Endpoint Priority

Build in this exact order:

```text
1. GET /api/health
2. POST /api/resume/upload
3. POST /api/interview/start
4. POST /api/interview/question
5. POST /api/audio/transcribe
6. POST /api/interview/evaluate
7. POST /api/interview/final-report
8. GET /api/interview/{session_id}/scorecard
9. GET /api/interview/history
10. GET /api/usage
```

---

# 21. Example Complete Interview API Sequence

```text
POST /api/resume/upload
   → returns resume_id

POST /api/interview/start
   → returns session_id

POST /api/interview/question
   → returns question_id + audio_url

User records answer

POST /api/audio/transcribe
   → returns answer_id + transcript

POST /api/interview/evaluate
   → returns score_id + feedback + follow_up

POST /api/interview/question
   → returns next question

Repeat until done

POST /api/interview/{session_id}/complete

POST /api/interview/final-report
   → returns final scorecard

GET /api/interview/{session_id}/scorecard
   → dashboard view
```

---

# 22. OpenAPI Tag Structure

Recommended FastAPI tags:

```python
tags_metadata = [
    {
        "name": "System",
        "description": "Health check and service metadata"
    },
    {
        "name": "Users",
        "description": "Authenticated user profile and usage"
    },
    {
        "name": "Resumes",
        "description": "Resume upload, parsing, and deletion"
    },
    {
        "name": "Interviews",
        "description": "Interview session lifecycle and question generation"
    },
    {
        "name": "Audio",
        "description": "Audio upload and transcription"
    },
    {
        "name": "Evaluation",
        "description": "Answer evaluation and final scorecards"
    }
]
```

---

# 23. Final Notes

This API design intentionally separates:

```text
Question generation
Audio transcription
Answer evaluation
Final report generation
```

This separation makes the system easier to debug, cheaper to control, and more flexible for future features like streaming responses, chunked TTS, company-specific modes, and white-label APIs.

For MVP, keep the backend simple but production-style:

```text
FastAPI routes
Pydantic schemas
Service layer
Repository/database layer
Auth middleware
Rate limit middleware
External API wrappers
Structured logging
```
