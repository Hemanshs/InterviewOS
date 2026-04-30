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

## Phase Status

| Phase | Status |
| --- | --- |
| Phase 1.1 FastAPI backend scaffold | Complete |
| Phase 1.2 Resume upload and parsing | Pending |
| Phase 1.3 Interview session APIs | Pending |
| Phase 1.4 Audio transcription APIs | Pending |
| Phase 1.5 Evaluation and feedback APIs | Pending |
| Phase 1.6 Account and usage APIs | Pending |
