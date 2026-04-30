# Project Context — AI Voice Product Discussion

## Background

I initially wanted to build a product around voice cloning using ElevenLabs. The idea was:

- A user records or uploads their voice.
- The system clones/mimics that voice.
- The cloned voice can then be used to generate speech from text.
- Multiple users could clone and use their own voices.
- The product would be browser-based as a web app.

The first proposed direction was a multi-user voice cloning platform powered by ElevenLabs.

---

## Original Voice Cloning Platform Idea

### Core Flow

```text
User records/uploads voice sample
        ↓
Backend sends audio to ElevenLabs voice cloning API
        ↓
ElevenLabs returns voice_id
        ↓
System stores voice_id against user account
        ↓
User enters text
        ↓
Backend calls ElevenLabs TTS API using voice_id
        ↓
Generated audio is returned
        ↓
User can play, download, or share audio
```

### Suggested Tech Stack

```text
Frontend: Next.js / React
Backend: FastAPI or Node.js
Voice API: ElevenLabs
Database: PostgreSQL
Storage: AWS S3 / Cloudflare R2
Authentication: Supabase Auth / Clerk
```

### Useful Features

- Voice upload or browser recording
- Voice clone creation
- Text-to-speech generation
- Audio playback
- Audio download
- Voice library
- Consent checkbox
- Abuse-prevention policy

---

## Important Realization

In my current company, they are already using a similar kind of system.

The company use case is:

- Fintech knowledge is stored in a knowledge base.
- An AI assistant uses that knowledge.
- When someone calls, the agent speaks using ElevenLabs voice.
- The voice agent answers from stored company knowledge.

This is basically a **Voice RAG AI Assistant**.

---

## Company-Like Architecture

```text
User calls
   ↓
Speech-to-text
   ↓
AI understands the query
   ↓
Knowledge base / RAG search
   ↓
LLM generates answer
   ↓
ElevenLabs converts answer to speech
   ↓
Agent speaks back to caller
```

### Components

```text
Knowledge Base
Vector Database
LLM
Speech-to-Text
ElevenLabs Text-to-Speech
Telephony Integration
Conversation Logs
Admin Dashboard
```

Because this is already being done in my company, I decided not to build the same product.

---

## Decision

Do **not** build:

```text
Generic voice cloning app
Generic ElevenLabs voice assistant
Generic Voice RAG fintech assistant
```

Reason:

- It is too close to the company’s existing work.
- It may not look unique.
- It may not strongly differentiate my portfolio.
- A simple voice clone app can feel basic.
- A generic RAG chatbot is already common.

---

## New Product Direction

The selected idea is:

# InterviewOS — AI Voice Interview Coach

This is an AI-powered, voice-based mock interview platform for Software Engineer / SDET / Backend Engineer preparation.

---

## Why This Product Is Better

This product is stronger because it combines:

```text
Voice AI
Speech-to-text
LLM reasoning
Resume parsing
Job description analysis
Real-time interview simulation
Answer evaluation
Scorecard generation
Dashboard
Database
Deployment
```

This makes it look like a serious SDE / AI engineering project rather than a basic wrapper around ElevenLabs.

---

## Core Product Concept

The user uploads:

- Resume
- Job description
- Target role

The AI then:

- Generates role-specific interview questions
- Asks questions using voice
- Records user’s spoken answer
- Converts speech to text
- Evaluates the answer
- Gives detailed feedback
- Asks follow-up questions
- Generates a final scorecard

---

## Core Flow

```text
User logs in
   ↓
Uploads resume and/or job description
   ↓
Selects interview type
   ↓
AI generates first question
   ↓
Question is spoken using ElevenLabs
   ↓
User answers through microphone
   ↓
Speech-to-text converts answer to text
   ↓
LLM evaluates the answer
   ↓
System gives feedback and score
   ↓
AI asks follow-up question
   ↓
Interview continues
   ↓
Final report is generated
```

---

## Target Users

Primary target:

```text
Software Engineer candidates
SDET candidates
Backend Engineer candidates
Students preparing for technical interviews
Candidates switching domains into software roles
```

Secondary target:

```text
People preparing for behavioral interviews
Fresh graduates
Bootcamp learners
International job seekers
```

---

## MVP Scope

### MVP Name

```text
InterviewOS — AI Voice Interview Coach
```

### MVP Features

1. User authentication
2. Resume upload
3. Job description upload
4. Interview type selection
5. AI-generated interview questions
6. Voice-based interviewer
7. Microphone answer recording
8. Speech-to-text transcription
9. AI answer evaluation
10. Scorecard and feedback

---

## Interview Types

Initial interview modes:

```text
SDE Interview
SDET Interview
Backend Engineer Interview
Behavioral Interview
Resume-Based Interview
Job Description-Based Interview
```

---

## Evaluation Criteria

The system should evaluate answers based on:

```text
Technical correctness
Clarity
Structure
Depth
Confidence
Relevance to question
Use of examples
Communication quality
Filler words
Conciseness
```

---

## Final Scorecard

The scorecard should include:

```text
Overall score
Technical score
Communication score
Confidence score
Strengths
Weaknesses
Suggested improvements
Recommended topics to revise
Question-by-question feedback
Transcript
```

---

## Killer Features To Add Later

After MVP, add:

```text
Real-time follow-up questions
Resume-based deep questioning
Company-specific interview mode
Amazon-style leadership principles mode
DSA explanation feedback
System design interview mode
SDET automation testing round
Voice confidence analysis
Interview history dashboard
Progress tracking
Peer comparison
Shareable interview report
```

---

## Recommended Tech Stack

### Frontend

```text
Next.js
React
Tailwind CSS
MediaRecorder API
```

### Backend

```text
FastAPI
Python
REST APIs
```

### AI / Voice

```text
OpenAI / Claude / Gemini for interview logic
Whisper / Deepgram for speech-to-text
ElevenLabs for voice output
```

### Database

```text
PostgreSQL
Supabase
```

### Storage

```text
Supabase Storage
AWS S3
Cloudflare R2
```

### Deployment

```text
Frontend: Vercel
Backend: Render / Railway / Fly.io
Database: Supabase
```

---

## Suggested Folder Structure

```text
interviewos-ai-voice-coach/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── interview.py
│   │   │   ├── resume.py
│   │   │   ├── audio.py
│   │   │   └── feedback.py
│   │   ├── services/
│   │   │   ├── llm_service.py
│   │   │   ├── speech_service.py
│   │   │   ├── voice_service.py
│   │   │   ├── resume_parser.py
│   │   │   └── evaluation_service.py
│   │   ├── models/
│   │   │   ├── interview_models.py
│   │   │   └── feedback_models.py
│   │   └── utils/
│   │       └── file_utils.py
│   │
│   ├── requirements.txt
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   ├── api-design.md
│   └── product-roadmap.md
│
├── README.md
└── .gitignore
```

---

## Core Backend APIs

```text
POST /api/resume/upload
POST /api/interview/start
POST /api/interview/question
POST /api/audio/transcribe
POST /api/interview/evaluate
POST /api/interview/final-report
GET  /api/interview/history
```

---

## Product Positioning

Use this positioning:

```text
InterviewOS is an AI-powered voice interview coach that helps software engineering candidates practice realistic interviews through voice-based conversations, resume-aware questioning, and detailed AI-generated feedback.
```

---

## Resume / Portfolio Pitch

Use this in resume:

```text
Built InterviewOS, an AI-powered voice interview coach using Next.js, FastAPI, OpenAI, Whisper, and ElevenLabs. Implemented resume-based interview question generation, microphone-based answer recording, speech-to-text transcription, LLM-based answer evaluation, and detailed performance scorecards.
```

---

## GitHub README Pitch

```text
InterviewOS is a voice-based AI mock interview platform for software engineering candidates. It simulates realistic interviews by asking role-specific questions in voice, recording user responses, transcribing them, evaluating answers using LLMs, and generating detailed scorecards with actionable feedback.
```

---

## Why This Is a Strong SDE Project

This project demonstrates:

```text
Full-stack development
API design
Authentication
File upload
Audio handling
LLM integration
Speech-to-text
Text-to-speech
Prompt engineering
Database modeling
System design
Deployment
Product thinking
```

---

## Important Safety / Ethics

Since this product uses voice AI, it should include:

```text
No unauthorized voice cloning
Clear user consent
No impersonation features
Voice used only for interviewer or approved user voices
Data deletion option
Privacy policy
Audio storage control
```

---

## Final Decision

Build:

```text
InterviewOS — AI Voice Interview Coach
```

Do not build:

```text
Generic ElevenLabs voice cloning platform
Generic company-style Voice RAG agent
```

This project is unique, useful, portfolio-friendly, and aligned with Software Engineer / AI Engineer career goals.
