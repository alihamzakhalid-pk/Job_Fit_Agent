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
CRITICAL TASK: Rewrite resume bullets to MAXIMIZE ATS score. EVERY RULE MUST BE FOLLOWED.

=== MANDATORY RULES (follow ALL or response is invalid) ===
1. EVERY bullet MUST start with: developed, engineered, built, designed, optimized, deployed, automated, achieved, implemented, increased, reduced, delivered
2. EVERY bullet MUST include AT LEAST ONE number/metric: %, X improvement, timeframe, quantity (e.g., 50%, 3x faster, 2M users, 6 months)
3. EVERY bullet MUST be EXACTLY 15-22 words (count every word carefully - no exceptions)
4. NEVER use: "worked on", "helped", "involved in", "responsible for", "participated", "assisted", "was part of"
5. MUST include 2-3 keywords from job description in EACH bullet
6. MUST show measurable IMPACT - not just tasks or duties

=== SCORING CRITERIA (ATS systems check for these) ===
✓ Power verb (developed, engineered, etc.) = +25 points
✓ Number/metric included = +25 points  
✓ No weak phrases = +20 points
✓ 15-22 word length = +15 points
✓ Technical keywords/acronyms = +15 points
TOTAL POSSIBLE = 100 points per bullet

=== STRICT EXAMPLES ===

❌ FAILS (all these are wrong):
- "Worked on backend development" (weak verb, no number, too short)
- "Developed machine learning models" (no metric, no keywords from job)
- "Built system that helped team with data" (weak phrase "helped", no specific impact)
- "Engineered solution improving performance by 40% across 5 systems" (22 words - MUST be 15-22)

✅ PASSES (follow this format):
- "Engineered FastAPI backend processing 2M+ requests/day with 40% latency reduction"
- "Optimized PostgreSQL queries reducing response time from 500ms to 50ms for 100K daily users"
- "Developed machine learning pipeline increasing model accuracy by 34% across 5 production systems"
- "Deployed containerized microservices reducing deployment time by 60% across 12 services"

=== INPUT DATA ===
ORIGINAL BULLETS TO REWRITE:
{original_bullets}

JOB DESCRIPTION (extract keywords from here):
{job_description}

CANDIDATE SKILLS:
{skill_gaps}

=== OUTPUT REQUIREMENT ===
Return ONLY this JSON structure (no other text):
{{
    "rewritten_bullets": [
        {{
            "original": "original text here",
            "rewritten": "OPTIMIZED TEXT - must follow ALL rules above, 15-22 words, power verb, number, keywords",
            "improvement_reason": "Why this scores higher (lists which rules it now follows)",
            "keywords_added": ["keyword1", "keyword2", "keyword3"]
        }}
    ],
    "interview_questions": [
        {{
            "question": "Complete question text",
            "category": "technical/behavioral/situational",
            "why_asked": "Why this matters for the role",
            "tip": "How to answer based on job requirements",
            "difficulty": "junior/mid/senior"
        }}
    ],
    "resume_summary": "2-3 sentence professional summary optimized for this role"
}}

VALIDATE BEFORE RETURNING: Check each rewritten bullet has a power verb, a number, 15-22 words, no weak phrases.
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

        # VALIDATION: Check if bullets were actually changed
        unchanged_count = sum(
            1 for orig, rewr in zip(original_bullets, rewritten_list)
            if orig.strip().lower() == rewr.strip().lower()
        )
        
        if unchanged_count > len(rewritten_list) * 0.5:  # If >50% unchanged
            print(f"   ⚠️  WARNING: {unchanged_count}/{len(rewritten_list)} bullets unchanged - LLM may have failed")

        # DEBUG: Show what was rewritten
        print(f"\n   📝 REWRITTEN BULLETS ({len(rewritten_list)}):")
        for i, (orig, rewr) in enumerate(zip(original_bullets[:3], rewritten_list[:3]), 1):
            print(f"      {i}. ORIG ({len(orig.split())}w): {orig[:55]}...")
            print(f"         NEW  ({len(rewr.split())}w): {rewr[:55]}...")
            if orig.strip().lower() == rewr.strip().lower():
                print(f"         ⚠️  UNCHANGED!")

        print("   → Scoring rewritten resume (after)...")
        after_result = score_full_resume(rewritten_list)
        ats_after = after_result["overall_score"]
        improvement = ats_after - ats_before
        print(f"   → ATS Score AFTER: {ats_after}/100")
        print(f"   → IMPROVEMENT: +{improvement} points")

        # SAFETY CHECK: If rewrite made it worse, use original bullets instead
        if ats_after < ats_before:
            print(f"   ⚠️  WARNING: Rewrite decreased ATS ({ats_before} → {ats_after})")
            print(f"   → Reverting to original bullets (keeping {ats_before}/100)")
            
            # Use original as "rewritten" to avoid negative improvement
            rewrite_data["rewritten_bullets"] = [
                {
                    "original": bullet,
                    "rewritten": bullet,
                    "improvement_reason": "Original already optimized",
                    "keywords_added": []
                }
                for bullet in original_bullets
            ]
            ats_after = ats_before
            improvement = 0
            after_result = before_result

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
