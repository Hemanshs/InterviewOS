# InterviewOS Frontend

## Phase 3.1 — Frontend

**Setup:**

```bash
cd frontend
npm install
cp .env.local.example .env.local
```

**Required `.env.local`:**

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

**Run backend first:**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Run frontend:**

```bash
cd frontend
npm run dev
```

**Open:** `http://localhost:3000/interview`

**Expected behavior:**

1. Page loads showing "InterviewOS" and "Start Mock Interview" button
2. Click button → shows "Preparing your question..."
3. Then shows "Generating interviewer voice..."
4. Then shows question card with text, focus areas, difficulty badge
5. Audio player appears — in dev mode shows mock URL notice
6. Reset button returns to idle state

## Phase 3.2 — Mic Recording + Transcription

**Testing with real mic:**

1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Open http://localhost:3000/interview
4. Click "Start Mock Interview"
5. Wait for question to appear
6. Click "Start Answer"
7. Allow mic permission when prompted
8. Speak your answer
9. Click "Stop Recording" or wait 60 seconds
10. Wait for transcription to complete
11. Transcript card appears with word count and filler word analysis

**Testing without real mic (curl simulation):**

```bash
# Create a small dummy audio file
echo "test audio" > /tmp/test.webm

# Simulate what the frontend sends
curl -X POST http://localhost:8000/api/audio/transcribe \
  -H "Authorization: Bearer mock_token" \
  -F "session_id=00000000-0000-0000-0000-000000000001" \
  -F "question_id=00000000-0000-0000-0000-000000000002" \
  -F "duration_seconds=15" \
  -F "language=en" \
  -F "audio_file=@/tmp/test.webm;type=audio/webm"
```

**Debugging mic permission issues:**

- Chrome: Address bar → lock icon → Site settings → Microphone → Allow
- Safari: Safari menu → Settings for this website → Microphone → Allow
- Firefox: Address bar → lock icon → Connection secure → Microphone → Allow
- If denied: must reload page after changing permission
- HTTPS required in production — localhost works without HTTPS in dev

## Phase 3.3 — Answer Evaluation

**Updated endpoint:** `POST /api/interview/evaluate`

**Test with curl:**

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

**Full flow to test manually:**

1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Open http://localhost:3000/interview
4. Click "Start Mock Interview" → question loads
5. Click "Start Answer" → record 5-10 seconds → "Stop Recording"
6. Wait for transcript card to appear
7. Click "Evaluate Answer" button (amber)
8. Wait for "Evaluating your response..." state
9. Evaluation card appears with 9 score chips + feedback

**Run backend tests:**

```bash
pytest tests/test_evaluation.py -v
```

## Phase 3.4 — Full Interview Loop

**Reset mock session counter (for testing):**

```bash
curl -X DELETE http://localhost:8000/api/interview/question/reset-mock/00000000-0000-0000-0000-000000000001
```

**Full 5-question test flow:**

1. Start backend + frontend
2. Open http://localhost:3000/interview
3. Click "Start Mock Interview"
4. Complete question 1: record → transcript → evaluate
5. Click "Next Question →" — verify question 2 loads with different text
6. Verify progress bar advances to "1 answered"
7. Verify "ANSWERS SO FAR" section shows Q1 with score
8. Complete questions 2-4 the same way
9. On question 5: "Finish Interview" button appears instead of "Next Question"
10. Click "Finish Interview" → completion screen appears
11. Verify all 5 answers in review section
12. Click "Start New Interview" → resets to idle

## Phase 3.5 — Final Scorecard

**Test with curl:**

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

**Manual full flow test:**

1. Start backend + frontend
2. Complete all 5 questions (or use "Finish Interview" early)
3. Interview complete screen appears
4. Click "Generate Final Scorecard" (amber button)
5. "Generating your scorecard..." state shows
6. FinalScorecard component renders with:
   - Large overall score (7.6)
   - 5 animated score bars
   - Strengths + weaknesses columns
   - Study recommendations pills
   - Question review list
   - Transcript toggle
7. "Start New Interview" resets everything to idle

**Run backend tests:**

```bash
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
3. Resume parsed card shows name, role, and key skills
4. Click `Start Mock Interview`
5. Questions are resume-aware and can reference your uploaded experience

**Run tests:**

```bash
pytest tests/test_resume_upload.py -v
```
