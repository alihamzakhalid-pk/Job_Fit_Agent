from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from graph.state import AgentState
from tools.retry_utils import llm_retry_decorator
from config import (
    LLM_MODEL,
    LLM_TEMPERATURE_PARSING,
    LLM_TIMEOUT,
    MAX_JOB_DESC_CHARS,
    SCORE_MISMATCH_THRESHOLD,
)
import json

# Initialize LLM once at module level
llm = ChatGroq(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE_PARSING,
    timeout=LLM_TIMEOUT,
)

GAP_ANALYSIS_PROMPT = """
You are an expert career coach and technical recruiter.
Analyze the candidate's profile against market demands and job requirements.
Return ONLY valid JSON. No explanation. No extra text.

CANDIDATE SKILLS:
{candidate_skills}

MARKET DEMANDED SKILLS (ranked by frequency):
{market_skills}

JOB DESCRIPTION:
{job_description}

Return this exact JSON:
{{
    "match_score": 50,
    "match_breakdown": {{
        "job_match": 50,
        "market_match": 50,
        "overall": 50
    }},
    "skills_you_have": [
        {{
            "name": "",
            "relevance": "one of: highly_relevant/relevant/low_relevance"
        }}
    ],
    "skill_gaps": [
        {{
            "name": "",
            "priority": "one of: critical/important/good_to_have",
            "reason": "why this skill is needed",
            "in_job_description": true,
            "market_frequency": 1,
            "estimated_learning_time": "2 weeks",
            "free_resource": {{
                "name": "",
                "url": ""
            }}
        }}
    ],
    "learning_roadmap": [
        {{
            "week": 1,
            "focus": "Main focus area for this week",
            "duration_hours": 15,
            "skills": ["skill1", "skill2"],
            "goal": "What should be accomplished by end of week",
            "daily_plan": [
                "Day 1-2: Learn concept X from resource Y",
                "Day 3-4: Build small project with tool Z",
                "Day 5: Practice exercises and review"
            ],
            "resources": [
                {{
                    "name": "Resource Name",
                    "type": "one of: tutorial/course/documentation/book/article/youtube",
                    "url": "https://...",
                    "duration": "2-3 hours",
                    "free": true
                }}
            ],
            "practice_project": "Optional small project to implement learning",
            "success_criteria": "How to know you've mastered this week's skills"
        }}
    ],
    "strengths": [],
    "quick_wins": [],
    "candidate_summary": "2-3 sentence honest assessment"
}}
"""

prompt = PromptTemplate(
    template=GAP_ANALYSIS_PROMPT,
    input_variables=["candidate_skills", "market_skills", "job_description"]
)


def extract_candidate_skills(parsed_resume: dict) -> str:
    skills = parsed_resume.get("skills", {})
    all_skills = []
    all_skills.extend(skills.get("technical", []))
    all_skills.extend(skills.get("tools", []))
    all_skills.extend(skills.get("languages", []))

    for proj in parsed_resume.get("projects", []):
        all_skills.extend(proj.get("technologies", []))

    all_skills = list(set(all_skills))
    return ", ".join(all_skills)


def extract_market_skills_text(market_skills: dict) -> str:
    skills = market_skills.get("skills", [])
    if not skills:
        return "No market data available"

    lines = []
    for skill in skills[:20]:
        name = skill.get("name", "")
        freq = skill.get("frequency", 0)
        importance = skill.get("importance", "")
        lines.append(f"- {name} (frequency: {freq}, importance: {importance})")

    return "\n".join(lines)


def calculate_match_score(candidate_skills: list, job_description: str) -> int:
    if not candidate_skills:
        return 0
    job_lower = job_description.lower()
    matches = sum(1 for s in candidate_skills if s.lower() in job_lower)
    return min(int((matches / max(len(candidate_skills), 1)) * 100), 100)


def clean_and_parse_json(raw_output: str) -> dict:
    raw_output = raw_output.replace("```json", "").replace("```", "").strip()
    start = raw_output.find("{")
    end = raw_output.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in output")
    return json.loads(raw_output[start:end])


def gap_analyzer_agent(state: AgentState) -> AgentState:
    """
    Agent 3: Analyzes skill gaps.
    Reads from state:  parsed_resume, market_skills, job_description
    Writes to state:   skill_gaps, match_score
    """

    print("\n🔎 Agent 3: Analyzing skill gaps...")

    try:
        parsed_resume = state["parsed_resume"]
        market_skills = state["market_skills"]
        job_description = state["job_description"]

        candidate_skills_text = extract_candidate_skills(parsed_resume)
        market_skills_text = extract_market_skills_text(market_skills)

        print(f"   → Candidate skills: {candidate_skills_text[:80]}...")
        print(f"   → Market skills to compare: {len(market_skills.get('skills', []))}")

        candidate_skills_list = parsed_resume.get("skills", {}).get("technical", [])
        quick_score = calculate_match_score(candidate_skills_list, job_description)
        print(f"   → Quick match score: {quick_score}%")

        print("   → Running deep gap analysis...")
        @llm_retry_decorator
        def analyze_gap_with_retry():
            chain = prompt | llm
            return chain.invoke({
                "candidate_skills": candidate_skills_text,
                "market_skills": market_skills_text,
                "job_description": job_description[:MAX_JOB_DESC_CHARS]
            })
        
        response = analyze_gap_with_retry()
        gap_data = clean_and_parse_json(response.content)

        llm_score = gap_data.get("match_score", 0)
        if abs(llm_score - quick_score) > SCORE_MISMATCH_THRESHOLD:
            print(f"   ⚠️  Score mismatch: LLM={llm_score}, Quick={quick_score} — averaging")
            gap_data["match_score"] = int((llm_score + quick_score) / 2)

        priority_order = {"critical": 0, "important": 1, "good_to_have": 2}
        gaps = gap_data.get("skill_gaps", [])
        gap_data["skill_gaps"] = sorted(
            gaps,
            key=lambda x: priority_order.get(x.get("priority", "good_to_have"), 2)
        )

        state["skill_gaps"] = gap_data
        state["match_score"] = gap_data.get("match_score", 0)

        critical = [g for g in gap_data["skill_gaps"] if g.get("priority") == "critical"]
        important = [g for g in gap_data["skill_gaps"] if g.get("priority") == "important"]

        print(f"✅ Agent 3: Complete")
        print(f"   Match Score: {gap_data.get('match_score')}%")
        print(f"   Critical gaps: {len(critical)}, Important gaps: {len(important)}")

    except Exception as e:
        print(f"❌ Agent 3 Error: {e}")
        state["skill_gaps"] = {}
        state["match_score"] = 0.0

    return state
