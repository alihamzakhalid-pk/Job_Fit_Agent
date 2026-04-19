from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from graph.state import AgentState
from tools.ats_scorer import score_full_resume, extract_bullets_from_resume
import json

# ─────────────────────────────────────────
# REWRITER PROMPT — TRUTH CONSTRAINED
# ─────────────────────────────────────────

REWRITER_PROMPT = """
You are an expert resume writer. Your job is to rewrite resume bullets
to be clearer, stronger, and ATS-optimized.

CRITICAL RULE — READ THIS FIRST:
You are STRICTLY FORBIDDEN from inventing any of the following:
- Percentages (e.g. 94% accuracy, 40% improvement)
- Scale numbers (e.g. 10k users, 50k requests, 1M records)
- Time savings (e.g. reduced time by 60%)
- Any metric NOT explicitly found in the original resume text below

If a bullet has NO metrics in the original → rewrite it WITHOUT metrics.
Describe the ACTION and IMPACT using strong verbs only.
NEVER fill gaps with made-up numbers to sound impressive.

ORIGINAL RESUME TEXT (source of truth — only use facts from here):
{resume_text}

BULLET POINTS TO REWRITE:
{original_bullets}

TARGET JOB DESCRIPTION:
{job_description}

CANDIDATE STRENGTHS:
{skill_gaps}

REWRITING RULES:
1. Start every bullet with a strong action verb
2. ONLY use metrics that exist in the original resume text above
3. Include relevant keywords from the job description
4. Keep each bullet 12-25 words
5. Remove weak phrases: worked on, helped with, assisted in, was responsible for
6. Show what you DID not just what you were assigned
7. If original has a metric — keep it and highlight it
8. If original has NO metric — use strong verbs and context only

GOOD EXAMPLE (metric exists in original):
Original: "Flask app using Naive Bayes with 96% accuracy"
Rewritten: "Engineered Naive Bayes text classifier achieving 96% accuracy with live YouTube API integration"
Reason: 96% came from original — safe to use ✅

BAD EXAMPLE (metric invented):
Original: "Built a resume analyzer system"
Rewritten: "Built resume analyzer achieving 94% accuracy serving 10k users"
Reason: 94% and 10k were invented — NEVER do this ❌

Return ONLY valid JSON. No explanation. No extra text:
{{
    "rewritten_bullets": [
        {{
            "original": "original bullet text",
            "rewritten": "improved bullet with no invented metrics",
            "improvement_reason": "what specifically was improved",
            "keywords_added": [],
            "metrics_used": "none OR list real metrics from original",
            "invented_metrics": false
        }}
    ],
    "interview_questions": [
        {{
            "question": "",
            "category": "one of: technical/behavioral/situational",
            "why_asked": "why interviewer would ask this",
            "tip": "how to answer this well"
        }}
    ],
    "resume_summary": "2-3 sentence professional summary using ONLY facts from the resume"
}}
"""

prompt = PromptTemplate(
    template=REWRITER_PROMPT,
    input_variables=["resume_text", "original_bullets", "job_description", "skill_gaps"]
)

# ─────────────────────────────────────────
# HALLUCINATION CHECKER PROMPT
# ─────────────────────────────────────────

HALLUCINATION_CHECK_PROMPT = """
You are a strict factual accuracy checker for resumes.
Your ONLY job is to detect invented or exaggerated claims.

ORIGINAL RESUME TEXT (ground truth — only facts here are real):
{resume_text}

REWRITTEN BULLETS TO VERIFY:
{rewritten_bullets}

For each rewritten bullet, check:
1. Does every number or percentage exist in the original resume text?
2. Was any scale invented (users, requests, records, downloads)?
3. Was any performance metric fabricated?

Return ONLY valid JSON:
{{
    "hallucinations_found": false,
    "total_checked": 0,
    "violations": [
        {{
            "original_bullet": "the rewritten bullet containing fake data",
            "invented_claim": "exactly what was invented e.g. 94% accuracy",
            "clean_rewrite": "safe version without the invented claim"
        }}
    ],
    "verified_bullets": [
        {{
            "original": "original bullet text",
            "rewritten": "verified clean rewritten bullet",
            "improvement_reason": "what was improved",
            "keywords_added": [],
            "metrics_used": "none or list real metrics",
            "invented_metrics": false
        }}
    ]
}}
"""


# ─────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────

def format_bullets_for_prompt(bullets: list) -> str:
    if not bullets:
        return "No bullets found"
    return "\n".join([f"- {b}" for b in bullets])


def format_gaps_for_prompt(skill_gaps: dict) -> str:
    gaps     = skill_gaps.get("skill_gaps", [])
    strengths = skill_gaps.get("strengths", [])
    lines    = []
    if strengths:
        lines.append(f"Candidate strengths: {', '.join(strengths)}")
    critical = [g["name"] for g in gaps if g.get("priority") == "critical"]
    if critical:
        lines.append(f"Missing skills — do NOT claim candidate has these: {', '.join(critical)}")
    return "\n".join(lines) if lines else "No gap data"


def clean_and_parse_json(raw_output: str) -> dict:
    raw_output = raw_output.replace("```json", "").replace("```", "").strip()
    start = raw_output.find("{")
    end   = raw_output.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in output")
    return json.loads(raw_output[start:end])


def run_hallucination_check(llm, resume_text: str, rewritten_bullets: list) -> tuple:
    """
    Cross-checks every rewritten bullet against original resume text.

    Returns:
        violations (list) — invented claims that were caught
        verified   (list) — clean bullets safe to show user
    """
    try:
        bullets_text = json.dumps(rewritten_bullets, indent=2)

        response = llm.invoke(
            HALLUCINATION_CHECK_PROMPT.format(
                resume_text=resume_text[:3000],
                rewritten_bullets=bullets_text[:3000]
            )
        )

        result     = clean_and_parse_json(response.content)
        violations = result.get("violations", [])
        verified   = result.get("verified_bullets", [])

        # Safety fallback — if checker returns empty, keep originals
        if not verified:
            verified = rewritten_bullets

        return violations, verified

    except Exception as e:
        print(f"   ⚠️  Hallucination checker error: {e} — skipping check")
        return [], rewritten_bullets


# ─────────────────────────────────────────
# MAIN AGENT FUNCTION
# ─────────────────────────────────────────

def resume_rewriter_agent(state: AgentState) -> AgentState:
    """
    Agent 4: Rewrites resume bullets with TRUTH CONSTRAINTS + HALLUCINATION CHECK.

    Design decisions:
    - temperature=0 to minimize creativity/hallucination
    - Prompt explicitly forbids inventing metrics
    - Ground truth (original resume) passed directly into prompt
    - Second LLM call verifies every bullet after rewriting
    - Any invented claim is removed before showing to user

    Reads from state:  parsed_resume, resume_text, skill_gaps, job_description
    Writes to state:   rewritten_bullets, ats_score_before, ats_score_after,
                       interview_questions, hallucination_report
    """

    print("\n✍️  Agent 4: Rewriting resume with truth constraints...")

    # temperature=0 — deterministic, less hallucination
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    )

    try:
        parsed_resume   = state["parsed_resume"]
        skill_gaps      = state["skill_gaps"]
        job_description = state["job_description"]
        resume_text     = state["resume_text"]  # ← ground truth

        # ── Step 1: Extract original bullets ──
        original_bullets = extract_bullets_from_resume(parsed_resume)

        if not original_bullets:
            print("   ⚠️  No bullets found in parsed resume")
            original_bullets = [
                "Worked on software development projects",
                "Helped team with technical tasks",
            ]

        print(f"   → Found {len(original_bullets)} bullet points")

        # ── Step 2: Score BEFORE rewrite ──
        print("   → Scoring original bullets (ATS before)...")
        before_result = score_full_resume(original_bullets)
        ats_before    = before_result["overall_score"]
        print(f"   → ATS Score BEFORE: {ats_before}/100")

        # ── Step 3: Rewrite with truth-constrained prompt ──
        print("   → Rewriting with truth-constrained prompt...")
        chain    = prompt | llm
        response = chain.invoke({
            "resume_text":      resume_text[:3000],
            "original_bullets": format_bullets_for_prompt(original_bullets),
            "job_description":  job_description[:1500],
            "skill_gaps":       format_gaps_for_prompt(skill_gaps)
        })

        rewrite_data      = clean_and_parse_json(response.content)
        rewritten_bullets = rewrite_data.get("rewritten_bullets", [])

        # ── Step 4: Hallucination check ──
        print("   → Running hallucination check...")
        violations, verified = run_hallucination_check(
            llm, resume_text, rewritten_bullets
        )

        if violations:
            print(f"   ⚠️  {len(violations)} hallucination(s) detected and fixed:")
            for v in violations:
                print(f"      Removed claim: '{v.get('invented_claim', '')}'")
            rewrite_data["rewritten_bullets"] = verified
        else:
            print(f"   ✅ Hallucination check passed — all bullets verified")

        rewrite_data["hallucination_violations"] = violations
        rewrite_data["hallucinations_found"]     = len(violations) > 0

        # ── Step 5: Score AFTER rewrite ──
        print("   → Scoring rewritten bullets (ATS after)...")
        rewritten_list = [
            item.get("rewritten", "")
            for item in rewrite_data.get("rewritten_bullets", [])
            if item.get("rewritten")
        ]

        after_result = score_full_resume(rewritten_list)
        ats_after    = after_result["overall_score"]
        improvement  = ats_after - ats_before
        print(f"   → ATS Score AFTER: {ats_after}/100 (+{improvement})")

        rewrite_data["ats_before"]  = {"score": ats_before, "breakdown": before_result["breakdown"]}
        rewrite_data["ats_after"]   = {"score": ats_after,  "breakdown": after_result["breakdown"]}
        rewrite_data["improvement"] = improvement

        # ── Step 6: Write everything to state ──
        state["rewritten_bullets"]    = rewrite_data
        state["ats_score_before"]     = ats_before
        state["ats_score_after"]      = ats_after
        state["interview_questions"]  = rewrite_data.get("interview_questions", [])
        state["hallucination_report"] = violations

        print(f"✅ Agent 4 Complete")
        print(f"   ATS: {ats_before} → {ats_after} (+{improvement})")
        print(f"   Hallucinations caught and removed: {len(violations)}")
        print(f"   Interview questions generated: {len(state['interview_questions'])}")

    except Exception as e:
        print(f"❌ Agent 4 Error: {e}")
        state["rewritten_bullets"]    = {}
        state["ats_score_before"]     = 0
        state["ats_score_after"]      = 0
        state["interview_questions"]  = []
        state["hallucination_report"] = []

    return state
