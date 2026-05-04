# InterviewOS - Deployment Guide

## Stack
- Frontend: Next.js -> Vercel
- Backend: FastAPI -> Render
- Database: PostgreSQL -> Supabase or Render PostgreSQL
- Auth: Supabase Auth

## 1. Supabase Setup
1. Create a project at https://supabase.com
2. In Settings -> API, collect:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_JWT_SECRET`
3. In Authentication -> Providers, enable Email
4. In Authentication -> URL Configuration:
   - Site URL: `https://your-app.vercel.app`
   - Redirect URLs: `https://your-app.vercel.app/interview`

## 2. Backend Deployment (Render)
1. Push the repo to GitHub
2. Create a new Render Web Service
3. Point it at the `backend` directory
4. Use `backend/render.yaml`
5. Set env vars in Render:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_JWT_SECRET`
   - `GEMINI_API_KEY`
   - `VERCEL_URL`
6. Deploy. Migrations run automatically before startup.

Backend URL example:
- `https://interviewos-api.onrender.com`

## 3. Frontend Deployment (Vercel)
1. Import the repo in Vercel
2. Set root directory to `frontend`
3. Set env vars:
   - `NEXT_PUBLIC_API_BASE_URL=https://interviewos-api.onrender.com`
   - `NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key`
4. Deploy
5. After frontend deploy, set `VERCEL_URL` on Render and redeploy backend

## 4. Run Migrations
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

## 5. Local Development
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

cd frontend
npm install
npm run dev
```

For local dev without real Supabase:
```env
DEV_AUTH_BYPASS=true
USE_MOCK_LLM=false
USE_MOCK_STT=false
USE_MOCK_TTS=true
```

## 6. Production Smoke Test Checklist
- `GET /api/health` returns 200
- `GET /api/health/deep` returns 200 and `database: ok`
- Frontend loads on Vercel
- Sign up and confirm email
- Log in and load `/interview`
- Upload a resume and verify parsing
- Start an interview
- Record, transcribe, and evaluate an answer
- Finish an interview and generate a final scorecard
- Refresh and verify recovery
- Log out and back in

## 7. Common Issues
- CORS errors:
  - Set `VERCEL_URL`
  - Confirm `ALLOWED_ORIGINS`
  - Redeploy backend after changes
- 401 on protected routes:
  - Check `SUPABASE_JWT_SECRET`
  - Check the frontend sends `Authorization: Bearer <token>`
- Database errors:
  - Confirm `DATABASE_URL` uses `+asyncpg`
  - Run `alembic upgrade head`
- Cold starts on free tier:
  - Expect the first request after idle to be slow
