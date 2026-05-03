# InterviewOS Backend

FastAPI backend scaffold for InterviewOS Phase 1.1.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
cd backend
uvicorn app.main:app --reload
```

## Test

```bash
cd backend
pytest tests/
```

## AI Providers

InterviewOS now uses Gemini for:

- Speech-to-text transcription
- Question generation
- Answer evaluation
- Final scorecard generation

ElevenLabs remains the separate TTS provider.

### Mock Mode

Use this during local development to keep the full MVP flow working without external API calls:

```bash
USE_MOCK_AI=true
USE_MOCK_STT=true
USE_MOCK_LLM=true
USE_MOCK_TTS=true
```

### Gemini Mode

To enable real Gemini-backed transcription and LLM behavior:

```bash
GEMINI_API_KEY=your_gemini_api_key
STT_PROVIDER=gemini
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_REPORT_MODEL=gemini-2.5-flash-lite
USE_MOCK_STT=false
USE_MOCK_LLM=false
```

If real STT mode is enabled without a Gemini key, `/api/audio/transcribe` returns `TRANSCRIPTION_FAILED` with:

```text
GEMINI_API_KEY is required when USE_MOCK_STT=false and STT_PROVIDER=gemini
```

If real LLM mode is enabled without a Gemini key, `/api/interview/question`, `/api/interview/evaluate`, and `/api/interview/final-report` return `LLM_FAILED` with:

```text
GEMINI_API_KEY is required when USE_MOCK_LLM=false and LLM_PROVIDER=gemini
```

## Phase 4.1 - Gemini Transcription

**Test with curl (mock mode):**

```bash
# Create a small test audio file
echo "test" > /tmp/test_answer.webm

# Send request
curl -X POST http://localhost:8000/api/audio/transcribe \
  -H "Authorization: Bearer mock_token" \
  -F "session_id=00000000-0000-0000-0000-000000000001" \
  -F "question_id=00000000-0000-0000-0000-000000000002" \
  -F "duration_seconds=30" \
  -F "language=en" \
  -F "audio_file=@/tmp/test_answer.webm;type=audio/webm"
```

**Run tests:**

```bash
pytest tests/test_audio_transcribe.py -v
```

**Test with curl (Gemini STT mode):**

```bash
export USE_MOCK_STT=false
export STT_PROVIDER=gemini
export GEMINI_API_KEY=your_gemini_api_key

curl -X POST http://localhost:8000/api/audio/transcribe \
  -H "Authorization: Bearer mock_token" \
  -F "session_id=00000000-0000-0000-0000-000000000001" \
  -F "question_id=00000000-0000-0000-0000-000000000002" \
  -F "duration_seconds=30" \
  -F "language=en" \
  -F "audio_file=@/tmp/test_answer.webm;type=audio/webm"
```

To return to mock mode, set `USE_MOCK_STT=true` and restart the backend.

## Gemini Question Generation

**Endpoint:** `POST /api/interview/question`

Mock mode keeps the current deterministic question bank. Real mode uses Gemini with the prompt builders in `app/prompts/question_prompts.py`.

**Test with curl (Gemini LLM mode):**

```bash
export USE_MOCK_LLM=false
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_gemini_api_key
```

```bash
curl -X POST http://localhost:8000/api/interview/question \
  -H "Authorization: Bearer mock_token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "00000000-0000-0000-0000-000000000001",
    "mode": "first",
    "include_voice": true
  }'
```

## Gemini Answer Evaluation

```bash
curl -X POST http://localhost:8000/api/interview/evaluate \
  -H "Authorization: Bearer mock_token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "00000000-0000-0000-0000-000000000001",
    "question_id": "00000000-0000-0000-0000-000000000002",
    "answer_id": "00000000-0000-0000-0000-000000000003",
    "generate_follow_up": true
  }'
```

## Gemini Final Report

```bash
curl -X POST http://localhost:8000/api/interview/final-report \
  -H "Authorization: Bearer mock_token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "00000000-0000-0000-0000-000000000001",
    "include_transcript": true,
    "include_recommendations": true
  }'
```

## ElevenLabs TTS

TTS remains unchanged and is controlled separately:

```bash
USE_MOCK_TTS=true
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

## Run Tests

```bash
pytest tests/test_resume_upload.py -v
pytest tests/test_audio_transcribe.py -v
pytest tests/test_evaluation.py -v
pytest tests/test_final_report.py -v
pytest tests/ -v --tb=short
```

## Phase 4.2 — Resume Upload

**Install new dependency:**

```bash
cd backend && pip install pymupdf==1.24.10
```

**Test resume upload:**

```bash
curl -X POST http://localhost:8000/api/resume/upload \
  -H "Authorization: Bearer mock_token" \
  -F "file=@/path/to/your/resume.pdf"
```

**Full flow:**

1. Open `/interview`
2. Upload PDF resume or click Skip
3. Resume parsed card shows name, role, and skills
4. Click `Start Interview`
5. Questions are resume-aware and can reference experience from the uploaded profile

**Run tests:**

```bash
pytest tests/test_resume_upload.py -v
```

## Phase Status

| Phase | Status |
| --- | --- |
| Phase 1.1 FastAPI backend scaffold | Complete |
| Phase 1.2 Resume upload and parsing | Complete |
| Phase 1.3 Interview session APIs | Pending |
| Phase 1.4 Audio transcription APIs | Pending |
| Phase 1.5 Evaluation and feedback APIs | Pending |
| Phase 1.6 Account and usage APIs | Pending |
