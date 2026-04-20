from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from graph.state import AgentState
from tools.ats_scorer import score_full_resume, extract_bullets_from_resume
from tools.retry_utils import llm_retry_decorator
from config import (
    LLM_MODEL,
    LLM_TEMPERATURE_REWRITING,
    LLM_TIMEOUT,
    MAX_JOB_DESC_CHARS,
    ATS_SCORING_CONFIG,
)
import json

# Initialize LLM once at module level (using rewriting temperature)
llm = ChatGroq(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE_REWRITING,
    timeout=LLM_TIMEOUT,
)

REWRITER_PROMPT = """
You are an EXPERT ATS-optimized resume writer. Your task: rewrite bullets to MAXIMIZE ATS score.

CRITICAL RULES (follow EXACTLY):
1. EVERY bullet MUST start with power verb: developed, engineered, built, designed, optimized, deployed, automated, achieved
2. EVERY bullet MUST include a NUMBER/METRIC: %, x improvement, timeframe, quantity
3. EVERY bullet MUST be 15-22 words (count carefully)
4. NEVER use weak phrases: "worked on", "helped", "involved in", "responsible for", "participated"
5. MUST include 2-3 keywords from job description per bullet
6. MUST show measurable IMPACT not just tasks

ORIGINAL BULLETS (optimize these):
{original_bullets}

JOB DESCRIPTION (extract keywords):
{job_description}

CANDIDATE PROFILE:
{skill_gaps}

REWRITE EXAMPLES:
❌ WEAK: "Worked on machine learning models for data analysis"
✅ STRONG: "Engineered 5 machine learning models improving prediction accuracy by 34%, reducing processing time by 40%"

❌ WEAK: "Responsible for backend development"
✅ STRONG: "Architected scalable backend system handling 2M+ requests/day using FastAPI and PostgreSQL"

GENERATE THIS JSON EXACTLY:
{{
    "rewritten_bullets": [
        {{
            "original": "original text",
            "rewritten": "NEW OPTIMIZED TEXT - 15-22 words, starts with power verb, has number, job keywords",
            "improvement_reason": "Why this is better for ATS",
            "keywords_added": ["keyword1", "keyword2"]
        }}
    ],
    "interview_questions": [
        {{
            "question": "Specific interview question",
            "category": "technical/behavioral/situational",
            "why_asked": "Why recruiter asks this",
            "tip": "How to answer well",
            "difficulty": "junior/mid/senior"
        }}
    ],
    "resume_summary": "2-3 sentence powerful summary"
}}
"""

prompt = PromptTemplate(
    template=REWRITER_PROMPT,
    input_variables=["original_bullets", "job_description", "skill_gaps"]
)


def format_bullets_for_prompt(bullets: list) -> str:
    if not bullets:
        return "No bullets found"
    return "\n".join([f"- {b}" for b in bullets])


def format_gaps_for_prompt(skill_gaps: dict) -> str:
    gaps = skill_gaps.get("skill_gaps", [])
    strengths = skill_gaps.get("strengths", [])
    lines = []
    if strengths:
        lines.append(f"Candidate strengths: {', '.join(strengths)}")
    critical = [g["name"] for g in gaps if g.get("priority") == "critical"]
    if critical:
        lines.append(f"Critical gaps to avoid overstating: {', '.join(critical)}")
    return "\n".join(lines) if lines else "No gap data"


def clean_and_parse_json(raw_output: str) -> dict:
    raw_output = raw_output.replace("```json", "").replace("```", "").strip()
    start = raw_output.find("{")
    end = raw_output.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in output")
    return json.loads(raw_output[start:end])


def resume_rewriter_agent(state: AgentState) -> AgentState:
    """
    Agent 4: Rewrites resume bullets + scores ATS + generates questions.
    Reads from state:  parsed_resume, skill_gaps, job_description
    Writes to state:   rewritten_bullets, ats_score_before, ats_score_after, interview_questions
    """

    print("\n✍️  Agent 4: Rewriting resume + scoring ATS...")

    try:
        parsed_resume = state["parsed_resume"]
        skill_gaps = state["skill_gaps"]
        job_description = state["job_description"]

        original_bullets = extract_bullets_from_resume(parsed_resume)

        if not original_bullets:
            print("   ⚠️  No bullets found — using placeholder bullets")
            original_bullets = [
                "Developed backend systems processing 100K+ transactions",
                "Engineered machine learning pipeline improving accuracy by 25%",
                "Optimized database queries reducing latency by 60%"
            ]

        print(f"   → Found {len(original_bullets)} bullet points")

        print("   → Scoring original resume (before)...")
        before_result = score_full_resume(original_bullets)
        ats_before = before_result["overall_score"]
        print(f"   → ATS Score BEFORE: {ats_before}/100")

        print("   → Rewriting bullets with LLM (with retry)...")
        rewrite_attempts = 0
        rewrite_data = None
        last_error = None
        
        while rewrite_attempts < 3:
            try:
                rewrite_attempts += 1
                @llm_retry_decorator
                def rewrite_with_retry():
                    chain = prompt | llm
                    return chain.invoke({
                        "original_bullets": format_bullets_for_prompt(original_bullets),
                        "job_description": job_description[:MAX_JOB_DESC_CHARS],
                        "skill_gaps": format_gaps_for_prompt(skill_gaps)
                    })
                
                response = rewrite_with_retry()
                rewrite_data = clean_and_parse_json(response.content)
                break  # Success - exit retry loop
                
            except json.JSONDecodeError as e:
                last_error = f"JSON parsing failed (attempt {rewrite_attempts}/3): {e}"
                if rewrite_attempts < 3:
                    print(f"   ⚠️  {last_error} — retrying...")
                    continue
                raise
            except Exception as e:
                last_error = f"LLM call failed (attempt {rewrite_attempts}/3): {e}"
                if rewrite_attempts < 3:
                    print(f"   ⚠️  {last_error} — retrying...")
                    continue
                raise

        if not rewrite_data or "rewritten_bullets" not in rewrite_data:
            raise ValueError("Invalid rewrite response structure")

        rewritten_list = [
            item["rewritten"]
            for item in rewrite_data.get("rewritten_bullets", [])
            if item.get("rewritten")
        ]

        if not rewritten_list:
            raise ValueError("No rewritten bullets generated")

        print("   → Scoring rewritten resume (after)...")
        after_result = score_full_resume(rewritten_list)
        ats_after = after_result["overall_score"]
        improvement = ats_after - ats_before
        print(f"   → ATS Score AFTER: {ats_after}/100")
        print(f"   → IMPROVEMENT: +{improvement} points")

        rewrite_data["ats_before"] = {"score": ats_before, "breakdown": before_result["breakdown"]}
        rewrite_data["ats_after"] = {"score": ats_after, "breakdown": after_result["breakdown"]}
        rewrite_data["improvement"] = improvement

        state["rewritten_bullets"] = rewrite_data
        state["ats_score_before"] = ats_before
        state["ats_score_after"] = ats_after
        state["interview_questions"] = rewrite_data.get("interview_questions", [])

        print(f"✅ Agent 4: Complete")
        print(f"   ATS: {ats_before} → {ats_after} (+{improvement})")
        print(f"   Interview questions: {len(state['interview_questions'])}")

    except Exception as e:
        print(f"❌ Agent 4 CRITICAL ERROR: {e}")
        print(f"   Falling back to placeholder results...")
        
        # Create fallback rewritten bullets from original
        state["ats_score_before"] = 0
        state["ats_score_after"] = 0
        state["rewritten_bullets"] = {
            "rewritten_bullets": [],
            "interview_questions": [],
            "resume_summary": "Professional with diverse experience",
            "ats_before": {"score": 0, "breakdown": []},
            "ats_after": {"score": 0, "breakdown": []},
            "improvement": 0
        }
        state["interview_questions"] = []
        
        # Mark state so orchestrator knows this needs attention
        state["resume_rewriter_error"] = str(e)

    return state
