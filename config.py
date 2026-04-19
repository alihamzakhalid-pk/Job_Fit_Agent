"""
Centralized configuration for Job Fit Agent.
All hardcoded values, model names, and API settings go here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# LLM CONFIGURATION
# ============================================================================
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE_PARSING = 0  # For resume parsing, gap analysis (deterministic)
LLM_TEMPERATURE_REWRITING = 0.3  # For resume rewriting (slightly creative)
LLM_TEMPERATURE_REFLECTION = 0.5  # For self-reflection (balanced - allows variation)
LLM_TIMEOUT = 30  # seconds - prevent hanging on slow API

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ============================================================================
# VALIDATION & LIMITS
# ============================================================================
MIN_RESUME_CHARS = 100
MAX_RESUME_CHARS = 10000
MIN_JOB_DESC_CHARS = 50
MAX_JOB_DESC_CHARS = 50000

# ============================================================================
# MARKET RESEARCH SETTINGS
# ============================================================================
SEARCH_RESULTS_PER_QUERY = 4  # Results per search query
SEARCH_QUERIES_COUNT = 3  # Number of search queries to run
MAX_MARKET_SKILLS = 20  # Max skills to extract from market research
SEARCH_RESULTS_MAX_CHARS = 4000  # Max chars for combined search results

# ============================================================================
# GAP ANALYSIS SETTINGS
# ============================================================================
SCORE_MISMATCH_THRESHOLD = 40  # If LLM score differs by >40 from quick score, handle it

# ============================================================================
# ATS SCORING WEIGHTS
# ============================================================================
ATS_SCORING_CONFIG = {
    "action_verb_points": 25,
    "quantification_points": 25,
    "no_weak_phrases_points": 20,
    "length_points": 15,
    "technical_keywords_points": 15,
    "ideal_word_count_min": 15,
    "ideal_word_count_max": 30,
}

# ============================================================================
# RETRY CONFIGURATION
# ============================================================================
MAX_RETRIES = 3  # Max retry attempts for LLM calls
RETRY_BACKOFF_MULTIPLIER = 1  # Exponential backoff multiplier
RETRY_MIN_WAIT = 2  # Minimum seconds to wait before retry
RETRY_MAX_WAIT = 10  # Maximum seconds to wait before retry

# ============================================================================
# API CONFIGURATION
# ============================================================================
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ============================================================================
# CORS CONFIGURATION
# ============================================================================
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
