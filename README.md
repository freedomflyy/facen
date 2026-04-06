# Facen

A classroom attendance system based on face recognition, with student check-in, teacher session publishing, admin management, liveness detection, and geofence validation.

This repository has been prepared for public showcase use:

- local database files, uploaded face photos, IDE settings, `node_modules`, and report materials are ignored
- JWT secret and database path are configurable through environment variables
- demo seed data has been replaced with neutral sample accounts

## Features

- Student flow: sign up, capture photo, verify session code, liveness detection, face matching, attendance history
- Teacher flow: create attendance sessions, target classes, review attendance, manual check-in
- Admin flow: manage teachers, students, classes, class assignment, and attendance records
- Validation: session timeout, geofence checks, face embedding comparison

## Tech Stack

- Frontend: Vue 3, Vite, Element Plus, Axios, face-api.js
- Backend: FastAPI, SQLModel, SQLite, JWT
- Vision: InsightFace, OpenCV, ONNX Runtime, MiniFASNet

## Project Structure

```text
.
- backend/
  - main.py
  - models.py
  - auth.py
  - database.py
  - init_data.py
  - resources/
- frontend/
  - src/views/
  - src/components/
  - public/models/
- README.md
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python init_data.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

## Demo Accounts

The seed script creates these local demo accounts:

- `root / root`
- `teacher_a / 123456`
- `teacher_b / 123456`
- `student_01` to `student_04` / `123456`

These are for local demo use only and should be replaced before any real deployment.

## Environment Variables

See `backend/.env.example`:

```env
FACEN_SECRET_KEY=replace-with-a-random-secret
FACEN_JWT_ALGORITHM=HS256
FACEN_ACCESS_TOKEN_EXPIRE_MINUTES=30
FACEN_DB_PATH=database.db
```

## Notes For GitHub Showcase

- Do not commit real face images, local databases, or screenshots with real names or student IDs
- The repository currently keeps model files for easier local reproduction
- Some legacy comments in backend code still contain historical encoding issues, but runtime behavior is unaffected

## Suggested Repository Description

Face recognition classroom attendance system built with Vue 3 and FastAPI, featuring liveness detection and geofence-based check-in.

## Suggested Screenshot Plan

- Login page with generic demo accounts only
- Teacher dashboard showing a sample attendance session
- Student check-in flow with blurred or synthetic face data
- Admin dashboard with anonymized class and user records
