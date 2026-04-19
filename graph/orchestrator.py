from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from graph.state import AgentState
from agents.resume_parser import resume_parser_agent
from agents.market_research import market_research_agent
from agents.gap_analyzer import gap_analyzer_agent
from agents.resume_rewriter import resume_rewriter_agent
from tools.retry_utils import llm_retry_decorator
from config import LLM_MODEL, LLM_TEMPERATURE_PARSING, LLM_TEMPERATURE_REFLECTION, LLM_TIMEOUT, MIN_RESUME_CHARS, MIN_JOB_DESC_CHARS
import json
import hashlib

# Initialize LLM for orchestrator
llm = ChatGroq(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE_PARSING,
    timeout=LLM_TIMEOUT,
)

# Separate LLM for self-reflection (with variation)
llm_reflection = ChatGroq(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE_REFLECTION,
    timeout=LLM_TIMEOUT,
)


def hash_inputs(resume_text: str, job_description: str) -> dict:
    """
    Create reproducible hashes of inputs to verify consistency.
    Use this to debug why results differ.
    """
    resume_hash = hashlib.md5(resume_text.encode()).hexdigest()[:8]
    job_hash = hashlib.md5(job_description.encode()).hexdigest()[:8]
    combined_hash = hashlib.md5(
        f"{resume_text}{job_description}".encode()
    ).hexdigest()[:8]
    
    return {
        "resume_hash": resume_hash,
        "job_hash": job_hash,
        "combined_hash": combined_hash
    }



def self_reflection_node(state: AgentState) -> AgentState:
    """
    Checks quality of all agent outputs.
    Decides if any agent needs to retry.
    """

    print("\n🧠 Orchestrator: Running self reflection...")

    match_score = state.get("match_score", 0)
    skill_gaps = state.get("skill_gaps", {})
    market_skills = state.get("market_skills", {})
    ats_before = state.get("ats_score_before", 0)
    ats_after = state.get("ats_score_after", 0)

    reflection_prompt = f"""
    You are a quality checker for an AI agent system.
    Review these outputs and decide if quality is acceptable.
    Return ONLY valid JSON.

    AGENT OUTPUTS:
    - Match Score: {match_score}/100
    - Market Skills Found: {len(market_skills.get('skills', []))}
    - Skill Gaps Found: {len(skill_gaps.get('skill_gaps', []))}
    - ATS Before: {ats_before}/100
    - ATS After: {ats_after}/100
    - Has Learning Roadmap: {bool(skill_gaps.get('learning_roadmap'))}
    - Has Interview Questions: {bool(state.get('interview_questions'))}

    QUALITY RULES:
    1. Market skills should be at least 5
    2. Skill gaps should be at least 2
    3. ATS after should be higher than ATS before
    4. Match score should be between 10 and 95
    5. Learning roadmap must exist

    SCORING GUIDELINES:
    - 0.9-1.0: All rules met, excellent quality
    - 0.7-0.8: Most rules met, good quality
    - 0.5-0.6: Some rules missing, acceptable
    - Below 0.5: Critical issues, needs retry

    Evaluate the outputs above and return:
    {{
        "confidence_score": (CALCULATE THIS - float between 0 and 1 based on rules above),
        "quality_issues": ["list of any issues found"],
        "needs_retry": (true if confidence_score < 0.5, false otherwise),
        "retry_agent": "none or agent_name",
        "reflection_summary": "one sentence quality verdict based on the score"
    }}
    """

    try:
        @llm_retry_decorator
        def reflect_with_retry():
            return llm_reflection.invoke(reflection_prompt)
        
        response = reflect_with_retry()
        raw = response.content.replace("```json", "").replace("```", "").strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        reflection = json.loads(raw[start:end])

        # Get confidence score from LLM
        confidence = reflection.get("confidence_score", 0.5)
        
        # Validate and fallback to programmatic calculation if needed
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            # Calculate programmatically based on quality rules
            score = 0.0
            has_market_skills = len(market_skills.get('skills', [])) >= 5
            has_skill_gaps = len(skill_gaps.get('skill_gaps', [])) >= 2
            ats_improved = ats_after > ats_before
            match_in_range = 10 <= match_score <= 95
            has_roadmap = bool(skill_gaps.get('learning_roadmap'))
            has_questions = bool(state.get('interview_questions'))
            
            # Score: 1 point per rule met, divide by total rules
            rules_met = sum([
                has_market_skills,      # Rule 1
                has_skill_gaps,         # Rule 2
                ats_improved,           # Rule 3
                match_in_range,         # Rule 4
                has_roadmap,            # Rule 5
                has_questions           # Bonus: interview questions
            ])
            confidence = rules_met / 6.0
        
        state["confidence_score"] = confidence
        state["needs_retry"] = reflection.get("needs_retry", confidence < 0.5)
        state["retry_agent"] = reflection.get("retry_agent", "none")

        print(f"   → Confidence Score: {state['confidence_score']:.1%}")
        print(f"   → Quality Issues: {reflection.get('quality_issues', [])}")
        print(f"   → Needs Retry: {state['needs_retry']}")
        print(f"   → Verdict: {reflection.get('reflection_summary', '')}")

    except Exception as e:
        print(f"   ⚠️  Reflection error: {e} — defaulting to accept")
        state["confidence_score"] = 0.7
        state["needs_retry"] = False
        state["retry_agent"] = "none"

    return state


def compile_final_report(state: AgentState) -> AgentState:
    """
    Compiles all agent outputs into one clean final report.
    """

    print("\n📝 Orchestrator: Compiling final report...")

    skill_gaps = state.get("skill_gaps", {})
    market_skills = state.get("market_skills", {})
    rewritten = state.get("rewritten_bullets", {})
    questions = state.get("interview_questions", [])
    parsed_resume = state.get("parsed_resume", {})
    hallucination_report = state.get("hallucination_report", [])

    gaps = skill_gaps.get("skill_gaps", [])
    critical_gaps = [g for g in gaps if g.get("priority") == "critical"]
    important_gaps = [g for g in gaps if g.get("priority") == "important"]

    report = {
        "candidate_name": parsed_resume.get("personal_info", {}).get("name", "Candidate"),
        "match_score": state.get("match_score", 0),
        "ats_score_before": state.get("ats_score_before", 0),
        "ats_score_after": state.get("ats_score_after", 0),
        "ats_improvement": state.get("ats_score_after", 0) - state.get("ats_score_before", 0),
        "confidence_score": state.get("confidence_score", 0),
        "strengths": skill_gaps.get("strengths", []),
        "critical_gaps": critical_gaps,
        "important_gaps": important_gaps,
        "learning_roadmap": skill_gaps.get("learning_roadmap", []),
        "rewritten_bullets": rewritten.get("rewritten_bullets", []),
        "resume_summary": rewritten.get("resume_summary", ""),
        "interview_questions": questions,
        "sources": market_skills.get("sources", [])[:5],
        "candidate_summary": skill_gaps.get("candidate_summary", ""),
        "quick_wins": skill_gaps.get("quick_wins", []),
        "hallucinations_found": len(hallucination_report) > 0,
        "hallucination_report": hallucination_report,
        "hallucinations_removed": len(hallucination_report),
        "debug_input_hashes": state.get("input_hashes", {}),  # ← DEBUG: Include input fingerprints
    }

    state["final_report"] = report

    print(f"✅ Final report compiled for {report['candidate_name']}")
    print(f"   Match Score: {report['match_score']}%")
    print(f"   ATS: {report['ats_score_before']} → {report['ats_score_after']}")
    if hallucination_report:
        print(f"   Hallucinations caught & fixed: {len(hallucination_report)}")

    return state


def should_retry(state: AgentState) -> str:
    """
    Router — decides next step after reflection.
    """
    needs_retry = state.get("needs_retry", False)
    retry_agent = state.get("retry_agent", "none")
    confidence = state.get("confidence_score", 0.5)
    retry_count = state.get("retry_count", 0)

    if needs_retry and retry_count < 1:
        state["retry_count"] = retry_count + 1
        print(f"\n🔁 Retry triggered for: {retry_agent}")
        if retry_agent == "market_research":
            return "market_research"
        elif retry_agent == "gap_analyzer":
            return "gap_analyzer"
        elif retry_agent == "resume_rewriter":
            return "resume_rewriter"

    if confidence < 0.5 and retry_count < 1:
        state["retry_count"] = retry_count + 1
        print(f"\n🔁 Low confidence ({confidence}) — retrying gap analyzer")
        return "gap_analyzer"

    print(f"\n✅ Quality accepted (confidence: {confidence})")
    return "compile_report"


def build_graph():
    """
    Builds and compiles the LangGraph multi-agent pipeline.
    """
    graph = StateGraph(AgentState)

    graph.add_node("resume_parser", resume_parser_agent)
    graph.add_node("market_research", market_research_agent)
    graph.add_node("gap_analyzer", gap_analyzer_agent)
    graph.add_node("resume_rewriter", resume_rewriter_agent)
    graph.add_node("self_reflection", self_reflection_node)
    graph.add_node("compile_report", compile_final_report)

    graph.add_edge("resume_parser", "market_research")
    graph.add_edge("market_research", "gap_analyzer")
    graph.add_edge("gap_analyzer", "resume_rewriter")
    graph.add_edge("resume_rewriter", "self_reflection")

    graph.add_conditional_edges(
        "self_reflection",
        should_retry,
        {
            "market_research": "market_research",
            "gap_analyzer": "gap_analyzer",
            "resume_rewriter": "resume_rewriter",
            "compile_report": "compile_report"
        }
    )

    graph.add_edge("compile_report", END)
    graph.set_entry_point("resume_parser")

    return graph.compile()


def run_agent(resume_text: str, job_description: str) -> dict:
    """
    Main function to run the complete agent pipeline.
    """
    print("\n" + "="*50)
    print("🚀 STARTING JOB FIT AGENT")
    print("="*50)

    # ← INPUT VALIDATION
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty")
    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty")
    if len(resume_text) < MIN_RESUME_CHARS:
        raise ValueError(f"Resume too short (minimum {MIN_RESUME_CHARS} characters)")
    if len(job_description) < MIN_JOB_DESC_CHARS:
        raise ValueError(f"Job description too short (minimum {MIN_JOB_DESC_CHARS} characters)")

    # ← INPUT HASHING FOR DEBUGGING
    input_hashes = hash_inputs(resume_text, job_description)
    print(f"\n🔐 INPUT FINGERPRINT:")
    print(f"   Resume Hash:    {input_hashes['resume_hash']}")
    print(f"   Job Hash:       {input_hashes['job_hash']}")
    print(f"   Combined Hash:  {input_hashes['combined_hash']}")
    print(f"   (Use these to verify if inputs are identical across runs)")


    initial_state = {
        "resume_text": resume_text,
        "job_description": job_description,
        "parsed_resume": {},
        "market_skills": {},
        "skill_gaps": {},
        "match_score": 0.0,
        "rewritten_bullets": {},
        "ats_score_before": 0,
        "ats_score_after": 0,
        "interview_questions": [],
        "confidence_score": 0.0,
        "needs_retry": False,
        "retry_agent": "none",
        "retry_count": 0,
        "hallucination_report": [],
        "final_report": {},
        "messages": [],
        "input_hashes": input_hashes,  # ← DEBUG: Track input consistency
    }

    app = build_graph()
    final_state = app.invoke(initial_state)

    print("\n" + "="*50)
    print("✅ AGENT PIPELINE COMPLETE")
    print("="*50)

    return final_state["final_report"]
