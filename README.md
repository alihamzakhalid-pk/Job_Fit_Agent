# 🚀 JobFit Agent

**AI-Powered Resume Analysis & Optimization Platform**

An intelligent multi-agent system that analyzes your resume against job descriptions, identifies skill gaps, conducts live market research, and generates optimized resume bullets with ATS scoring.

[![Deployed on Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=flat-square&logo=vercel)](https://job-fit-agent.vercel.app)
[![Backend on Railway](https://img.shields.io/badge/Backend-Railway-0B0D0E?style=flat-square&logo=railway)](https://railway.app)
[![Made with React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Python FastAPI](https://img.shields.io/badge/FastAPI-0.104-009485?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)

---

## ✨ Features

### 🧠 Multi-Agent Workflow
- **Resume Parser** - Extracts skills, experience, education using LLMs
- **Market Research** - Searches 3 trending queries for live market demand
- **Gap Analyzer** - Compares your profile against market + job requirements
- **Resume Rewriter** - Generates optimized bullets with action verbs & quantification
- **Self Reflection** - Quality checks all outputs for consistency

### 🎯 Key Capabilities
✅ Resume upload & intelligent parsing  
✅ Job description analysis  
✅ Skill gap identification  
✅ Live market trend research  
✅ ATS-optimized bullet point generation  
✅ Resume scoring (0-100)  
✅ Comprehensive PDF report download  
✅ Full CORS-enabled REST API  

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (React/Vite)                   │
│          https://job-fit-agent.vercel.app               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Upload Resume → Job Description → Pipeline View │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │ Axios API Calls
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 Backend (FastAPI/Python)                 │
│      https://jobfitagent-production.up.railway.app      │
│  ┌──────────────────────────────────────────────────┐   │
│  │ /analyze → LangGraph Orchestrator                │   │
│  │ ├─ Resume Parser Agent                           │   │
│  │ ├─ Market Research Agent                         │   │
│  │ ├─ Gap Analyzer Agent                            │   │
│  │ ├─ Resume Rewriter Agent                         │   │
│  │ └─ Self Reflection Agent                         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
          ↓ Uses ↓
┌─────────────────────────────────────────────────────────┐
│        LLM: Groq (llama-3.3-70b-versatile)              │
│        Search: DuckDuckGo + Web Scraping               │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | React 18, Vite, Axios, CSS-in-JS |
| **Backend** | FastAPI, Python 3.11+ |
| **AI/LLMs** | Groq API, LangGraph, LangChain |
| **Search** | DuckDuckGo Search API |
| **PDF** | PyPDF2, reportlab |
| **Deployment** | Vercel (Frontend), Railway (Backend) |
| **DevOps** | Docker, GitHub Actions |

---

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- Groq API Key ([Get it here](https://console.groq.com))

### 1️⃣ Clone Repository
```bash
git clone https://github.com/yourusername/job_fit_agent.git
cd job_fit_agent
```

### 2️⃣ Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE_PARSING=0
LLM_TEMPERATURE_REWRITING=0.3
EOF

# Run backend
cd jobfit_react/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3️⃣ Frontend Setup
```bash
# Install dependencies
cd jobfit_react/frontend
npm install

# Create .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

### 4️⃣ Access Application
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## 🚀 Usage

### Web Interface
1. **Upload Resume** - PDF or text format
2. **Enter Job Description** - Paste the full job posting
3. **Analyze** - Wait for all 5 agents to complete (~60-90 seconds)
4. **Review Report** - See insights, gaps, and optimized bullets
5. **Download PDF** - Save the comprehensive analysis report

### API Endpoint

#### POST `/analyze`
Submit resume and job description for analysis.

```bash
curl -X POST http://localhost:8000/analyze \
  -F "resume=@resume.pdf" \
  -F "job_description=Senior Software Engineer at TechCorp..."
```

**Response:**
```json
{
  "success": true,
  "report": {
    "resume_data": {
      "skills": ["Python", "FastAPI", "React", ...],
      "experience": [...],
      "education": [...]
    },
    "market_research": {
      "trending_skills": [...],
      "market_demand": "High",
      "search_results": [...]
    },
    "gap_analysis": {
      "gaps": [...],
      "match_score": 72
    },
    "optimized_bullets": [
      {
        "original": "Worked on backend systems",
        "optimized": "Architected scalable FastAPI backend serving 10K+ daily users with 99.9% uptime",
        "ats_score": 89,
        "improvements": ["Action verb", "Quantification", "Technical keywords"]
      },
      ...
    ],
    "self_reflection": {
      "quality_checks": [...],
      "overall_quality_score": 8.5
    }
  }
}
```

#### GET `/`
Health check endpoint.

```bash
curl http://localhost:8000/
# Response: {"status": "Job Fit Agent API running"}
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# LLM Settings
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE_PARSING = 0          # Deterministic
LLM_TEMPERATURE_REWRITING = 0.3      # Slightly creative

# Validation Limits
MAX_RESUME_CHARS = 10000
MAX_JOB_DESC_CHARS = 50000
MIN_JOB_DESC_CHARS = 50

# Market Research
SEARCH_QUERIES_COUNT = 3
SEARCH_RESULTS_PER_QUERY = 4

# ATS Scoring
ATS_SCORING_CONFIG = {
    "action_verb_points": 25,
    "quantification_points": 25,
    "no_weak_phrases_points": 20,
    "length_points": 15,
    "technical_keywords_points": 15,
}
```

---

## 🌍 Environment Variables

### Backend (.env)
```bash
# Required
GROQ_API_KEY=gsk_xxxxxxxxxxxxxx
LLM_MODEL=llama-3.3-70b-versatile

# Optional
LLM_TEMPERATURE_PARSING=0
LLM_TEMPERATURE_REWRITING=0.3
LLM_TIMEOUT=30
```

### Frontend (.env.local)
```bash
VITE_API_URL=https://jobfitagent-production.up.railway.app
```

### CORS Configuration
Backend automatically allows requests from:
- `https://job-fit-agent.vercel.app` (Production)
- `http://localhost:5173` (Dev Frontend)
- `http://localhost:3000` (Alternative)

---

## 📁 Project Structure

```
job_fit_agent/
├── agents/                          # Multi-agent modules
│   ├── resume_parser.py            # Parse resumes
│   ├── market_research.py          # Research skills
│   ├── gap_analyzer.py             # Compare gaps
│   ├── resume_rewriter.py          # Optimize bullets
│   └── __init__.py
│
├── graph/                           # LangGraph orchestration
│   ├── orchestrator.py             # Agent workflow
│   ├── state.py                    # State management
│   └── __init__.py
│
├── tools/                           # Utility functions
│   ├── pdf_extractor.py            # Extract PDF text
│   ├── ats_scorer.py               # Score resumes
│   ├── search_tool.py              # DuckDuckGo search
│   └── retry_utils.py              # Retry logic
│
├── jobfit_react/
│   ├── backend/
│   │   └── main.py                 # FastAPI server
│   │
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx             # Main component
│       │   ├── components/
│       │   │   ├── UploadSection.jsx
│       │   │   ├── Pipeline.jsx
│       │   │   └── Dashboard.jsx
│       │   └── index.css
│       ├── vite.config.js
│       └── package.json
│
├── config.py                        # Central configuration
├── requirements.txt                 # Python dependencies
└── Dockerfile                       # Docker configuration
```

---

## 🚢 Deployment

### Frontend (Vercel)

```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy to Vercel"
git push

# 2. Connect to Vercel
# - Import repo from GitHub
# - Root Directory: jobfit_react/frontend
# - Build Command: npm run build
# - Output Directory: dist

# 3. Set Environment Variable
# VITE_API_URL = https://jobfitagent-production.up.railway.app
```

### Backend (Railway)

```bash
# 1. Connect Railway to GitHub
# - Select this repository
# - Root Directory: jobfit_react/backend

# 2. Add Environment Variables in Railway Dashboard
GROQ_API_KEY = your_key_here
LLM_MODEL = llama-3.3-70b-versatile

# 3. Railway auto-deploys on git push
git push
```

### Docker (Local)

```bash
# Build image
docker build -t jobfit-agent .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  jobfit-agent
```

---

## 🔧 Troubleshooting

### CORS Error
**Error:** `Access-Control-Allow-Origin header is missing`

**Solution:** Ensure backend has correct CORS origins in `main.py`:
```python
allow_origins=[
    "https://job-fit-agent.vercel.app",
    "http://localhost:5173",
]
```

### API URL Issues
**Error:** `Invalid job description: too long`

**Solution:** Check `MAX_JOB_DESC_CHARS` in `config.py` (default: 50000)

### Network Error
**Error:** `Network error — is the backend running?`

**Solution:** 
1. Verify backend is running
2. Check `VITE_API_URL` environment variable
3. Test API: `curl http://localhost:8000/`

### PDF Extraction Issues
**Error:** `Failed to extract resume text`

**Solution:**
- Ensure PDF is text-based (not image-based)
- Try converting to PDF/A format
- Max file size: 10MB

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Average Analysis Time | 60-90 seconds |
| Resume Upload Limit | 10MB |
| Max Job Description | 50,000 chars |
| ATS Score Range | 0-100 |
| Market Research Queries | 3 |
| API Response Time | <2s (avg) |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Development Guidelines
- Follow PEP 8 for Python
- Use ESLint for JavaScript/React
- Add tests for new features
- Update README for API changes

---

## 📝 Roadmap

- [ ] Multi-language resume support
- [ ] LinkedIn profile import
- [ ] Interview prep recommendations
- [ ] Salary negotiation insights
- [ ] Real-time collaboration features
- [ ] Mobile app (React Native)
- [ ] Advanced ATS scoring with ML
- [ ] Competitor resume analysis

---

## 📜 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Ali Hamza**
- GitHub: [@alihamza](https://github.com/alihamza)
- Email: contact@alihamza.dev

---

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- [Groq](https://groq.com) for fast LLM inference
- [FastAPI](https://fastapi.tiangolo.com) for API framework
- [React](https://react.dev) for UI library

---

## 📞 Support

For issues, questions, or suggestions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Open an [Issue](https://github.com/yourusername/job_fit_agent/issues)
3. Start a [Discussion](https://github.com/yourusername/job_fit_agent/discussions)

---

## 🎯 Next Steps

1. **Get Groq API Key**: [console.groq.com](https://console.groq.com)
2. **Local Setup**: Follow [Installation](#-installation)
3. **Test API**: Visit `http://localhost:8000/docs`
4. **Upload Resume**: Use web interface at `http://localhost:5173`

**Happy analyzing!** 🚀

---

<div align="center">

Made with ❤️ by [Ali Hamza](https://github.com/alihamza)

[⬆ Back to top](#-jobfit-agent)

</div>