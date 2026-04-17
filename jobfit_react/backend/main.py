import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import traceback

app = FastAPI(title="Job Fit Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Job Fit Agent API running"}

def validate_job_description(job_desc: str) -> tuple[bool, str]:
    """
    Validate job description to detect garbage/invalid input.
    Returns (is_valid, error_message)
    """
    from config import MIN_JOB_DESC_CHARS, MAX_JOB_DESC_CHARS
    
    job_desc = job_desc.strip()
    
    # Check length
    if len(job_desc) < MIN_JOB_DESC_CHARS:
        return False, f"Job description too short (min {MIN_JOB_DESC_CHARS} characters)"
    
    if len(job_desc) > MAX_JOB_DESC_CHARS:
        return False, f"Job description too long (max {MAX_JOB_DESC_CHARS} characters)"
    
    # Check for garbage patterns (random characters, no spaces, etc)
    word_count = len(job_desc.split())
    if word_count < 5:
        return False, "Job description must contain at least 5 words"
    
    # Check if it's mostly garbage characters (not letters/numbers/punctuation)
    valid_chars = sum(1 for c in job_desc if c.isalnum() or c.isspace() or c in '.,;:!?-()[]{}')
    if valid_chars / len(job_desc) < 0.8:
        return False, "Job description contains too many invalid characters"
    
    # Check if it's real job description content (should contain common job keywords)
    job_keywords = ['job', 'role', 'position', 'responsibility', 'requirement', 'skill', 
                    'experience', 'qualification', 'education', 'work', 'team', 'project',
                    'technical', 'develop', 'manage', 'lead', 'design', 'implement']
    
    lower_text = job_desc.lower()
    keyword_matches = sum(1 for keyword in job_keywords if keyword in lower_text)
    
    # If very few job keywords found, might be garbage
    if keyword_matches < 2 and len(job_desc) < 200:
        return False, "Job description doesn't appear to be a real job posting"
    
    return True, ""


@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        from tools.pdf_extractor import extract_text_from_pdf
        from graph.orchestrator import run_agent
        from config import MIN_RESUME_CHARS, MAX_RESUME_CHARS

        # Validate job description first (before processing resume)
        is_valid_job, error_msg = validate_job_description(job_description)
        if not is_valid_job:
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid job description: {error_msg}"}
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await resume.read()
            tmp.write(content)
            tmp_path = tmp.name

        resume_text = extract_text_from_pdf(tmp_path)

        if not resume_text.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract text from PDF. Use a text-based PDF."}
            )
        
        # Validate resume length
        resume_chars = len(resume_text.strip())
        if resume_chars < MIN_RESUME_CHARS:
            return JSONResponse(
                status_code=400,
                content={"error": f"Resume too short (minimum {MIN_RESUME_CHARS} characters)"}
            )
        
        if resume_chars > MAX_RESUME_CHARS:
            return JSONResponse(
                status_code=400,
                content={"error": f"Resume too long (maximum {MAX_RESUME_CHARS} characters)"}
            )

        report = run_agent(resume_text, job_description)
        return JSONResponse(content={"success": True, "report": report})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
