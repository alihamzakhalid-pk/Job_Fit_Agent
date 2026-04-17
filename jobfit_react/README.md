# Job Fit Agent — React + FastAPI

## Project Structure
```
jobfit_react/
├── backend/
│   └── main.py          ← FastAPI server
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── index.css
    │   ├── main.jsx
    │   └── components/
    │       ├── UploadSection.jsx
    │       ├── Pipeline.jsx
    │       └── Dashboard.jsx
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## Setup — Run Both Servers

### Terminal 1 — Backend (FastAPI)
```bash
cd C:\path\to\job_fit_agent   # your existing project root
pip install fastapi uvicorn python-multipart
uvicorn jobfit_react.backend.main:app --reload --port 8000
```

### Terminal 2 — Frontend (React)
```bash
cd jobfit_react/frontend
npm install
npm run dev
```

### Open browser
```
http://localhost:5173
```

## How It Works
- React frontend (port 5173) calls FastAPI backend (port 8000)
- Vite proxy forwards /analyze requests to backend automatically
- Backend runs your existing LangGraph multi-agent pipeline
- Results stream back to the beautiful React dashboard
