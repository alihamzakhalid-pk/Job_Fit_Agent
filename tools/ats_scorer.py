# tools/ats_scorer.py

import re
from typing import List

# Keywords that ATS systems love
ACTION_VERBS = [
    "engineered", "developed", "built", "designed", "implemented",
    "optimized", "deployed", "automated", "improved", "reduced",
    "increased", "achieved", "delivered", "led", "created",
    "architected", "integrated", "migrated", "streamlined", "launched"
]

# ATS systems hate these weak phrases
WEAK_PHRASES = [
    "worked on", "helped with", "assisted in", "was responsible for",
    "involved in", "participated in", "contributed to", "tried to",
    "basically", "various", "several", "many tasks"
]

# Quantification patterns — ATS loves numbers
QUANTIFICATION_PATTERNS = [
    r'\d+%',           # percentages: 40%
    r'\d+x',           # multipliers: 3x
    r'\$\d+',          # money: $50k
    r'\d+k',           # thousands: 10k
    r'\d+ (users|requests|models|pipelines|services|teams)'
]


def score_bullet_point(bullet: str) -> dict:
    """
    Scores a single resume bullet point.
    Returns score breakdown.
    """
    bullet_lower = bullet.lower()
    score = 0
    feedback = []
    details = {}

    # Check 1: Starts with action verb (25 points)
    starts_with_action = any(
        bullet_lower.startswith(verb) for verb in ACTION_VERBS
    )
    if starts_with_action:
        score += 25
        details["action_verb"] = "✓"
    else:
        feedback.append("Start with a strong action verb")
        details["action_verb"] = "✗"

    # Check 2: Contains quantification (25 points)
    has_numbers = any(
        re.search(pattern, bullet, re.IGNORECASE)
        for pattern in QUANTIFICATION_PATTERNS
    )
    if has_numbers:
        score += 25
        details["quantification"] = "✓"
    else:
        feedback.append("Add numbers/metrics to quantify impact")
        details["quantification"] = "✗"

    # Check 3: No weak phrases (20 points)
    has_weak = any(phrase in bullet_lower for phrase in WEAK_PHRASES)
    if not has_weak:
        score += 20
        details["no_weak_phrases"] = "✓"
    else:
        feedback.append("Remove weak phrases like 'worked on' or 'helped with'")
        details["no_weak_phrases"] = "✗"

    # Check 4: Length is right (15 points)
    # ATS prefers 15-30 words
    word_count = len(bullet.split())
    if 15 <= word_count <= 30:
        score += 15
        details["length"] = f"✓ ({word_count}w)"
    elif word_count < 15:
        feedback.append(f"Too short ({word_count}w) — add more detail")
        details["length"] = f"✗ short ({word_count}w)"
    else:
        feedback.append(f"Too long ({word_count}w) — keep under 30 words")
        details["length"] = f"✗ long ({word_count}w)"

    # Check 5: Contains technical keywords (15 points)
    # Basic check — does it mention any tech?
    tech_patterns = [
        r'\b[A-Z][a-zA-Z]+\b',  # CamelCase words (PyTorch, FastAPI)
        r'\b[A-Z]{2,}\b'         # Acronyms (AWS, API, SQL)
    ]
    has_tech = any(
        len(re.findall(pattern, bullet)) > 0
        for pattern in tech_patterns
    )
    if has_tech:
        score += 15
        details["tech_keywords"] = "✓"
    else:
        feedback.append("Include specific technical tools or technologies")
        details["tech_keywords"] = "✗"

    return {
        "score": score,
        "feedback": feedback,
        "details": details
    }


def score_full_resume(bullets: List[str]) -> dict:
    """
    Scores all bullet points and returns overall ATS score.
    """
    if not bullets:
        return {"overall_score": 0, "breakdown": []}

    total_score = 0
    breakdown = []

    for bullet in bullets:
        result = score_bullet_point(bullet)
        total_score += result["score"]
        breakdown.append({
            "bullet": bullet,
            "score": result["score"],
            "feedback": result["feedback"]
        })

    # Average score across all bullets
    overall_score = int(total_score / len(bullets))

    return {
        "overall_score": overall_score,
        "breakdown": breakdown,
        "total_bullets": len(bullets)
    }


def extract_bullets_from_resume(parsed_resume: dict) -> List[str]:
    """
    Extracts all bullet points from parsed resume.
    """
    bullets = []

    # From experience
    for exp in parsed_resume.get("experience", []):
        bullets.extend(exp.get("responsibilities", []))
        bullets.extend(exp.get("achievements", []))

    # From projects
    for proj in parsed_resume.get("projects", []):
        desc = proj.get("description", "")
        if desc:
            bullets.append(desc)

    # Filter empty strings
    bullets = [b.strip() for b in bullets if b.strip()]

    return bullets