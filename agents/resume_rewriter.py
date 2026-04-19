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
You are an expert resume writer, ATS optimization specialist, AND interview coach.
Rewrite resume bullets to be ATS-optimized AND generate comprehensive interview prep questions.
Return ONLY valid JSON. No explanation. No extra text.

ORIGINAL BULLET POINTS:
{original_bullets}

TARGET JOB DESCRIPTION:
{job_description}

CANDIDATE STRENGTHS TO HIGHLIGHT:
{skill_gaps}

RESUME REWRITING RULES:
1. Start every bullet with a strong action verb
2. Add specific metrics and numbers where possible
3. Include relevant keywords from job description
4. Keep each bullet 15-25 words
5. Remove weak phrases like worked on or helped with
6. Show impact not just tasks

INTERVIEW QUESTIONS RULES:
Generate at least 10 most important interview questions that would REALLY be asked:
- 3-4 TECHNICAL questions (testing skills, tools, frameworks)
- 3-4 BEHAVIORAL questions (testing soft skills, leadership, collaboration)
- 2-3 SITUATIONAL questions (testing problem-solving, decision-making)
Each question should be:
- Directly related to the job description
- Challenging and realistic (what real interviewers ask)
- Testing either their strengths or skill gaps
- Clear and professional

Return this exact JSON:
{{
    "rewritten_bullets": [
        {{
            "original": "original bullet text",
            "rewritten": "improved bullet text",
            "improvement_reason": "why this is better",
            "keywords_added": []
        }}
    ],
    "interview_questions": [
        {{
            "question": "Full question text here",
            "category": "one of: technical/behavioral/situational",
            "why_asked": "why an interviewer would ask this question for this role",
            "tip": "how to answer this question well based on the job description",
            "difficulty": "one of: junior/mid/senior"
        }}
    ],
    "resume_summary": "A powerful 2-3 sentence professional summary for this specific job"
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
                "Worked on machine learning projects",
                "Helped team with data analysis tasks",
                "Participated in software development"
            ]

        print(f"   → Found {len(original_bullets)} bullet points")

        print("   → Scoring original resume (before)...")
        before_result = score_full_resume(original_bullets)
        ats_before = before_result["overall_score"]
        print(f"   → ATS Score BEFORE: {ats_before}/100")

        print("   → Rewriting bullets with LLM...")
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

        rewritten_list = [
            item["rewritten"]
            for item in rewrite_data.get("rewritten_bullets", [])
            if item.get("rewritten")
        ]

        print("   → Scoring rewritten resume (after)...")
        after_result = score_full_resume(rewritten_list)
        ats_after = after_result["overall_score"]
        print(f"   → ATS Score AFTER: {ats_after}/100")

        rewrite_data["ats_before"] = {"score": ats_before, "breakdown": before_result["breakdown"]}
        rewrite_data["ats_after"] = {"score": ats_after, "breakdown": after_result["breakdown"]}
        rewrite_data["improvement"] = ats_after - ats_before

        state["rewritten_bullets"] = rewrite_data
        state["ats_score_before"] = ats_before
        state["ats_score_after"] = ats_after
        state["interview_questions"] = rewrite_data.get("interview_questions", [])

        print(f"✅ Agent 4: Complete")
        print(f"   ATS: {ats_before} → {ats_after} (+{ats_after - ats_before})")
        print(f"   Interview questions: {len(state['interview_questions'])}")

    except Exception as e:
        print(f"❌ Agent 4 Error: {e}")
        state["rewritten_bullets"] = {}
        state["ats_score_before"] = 0
        state["ats_score_after"] = 0
        state["interview_questions"] = []

    return state
