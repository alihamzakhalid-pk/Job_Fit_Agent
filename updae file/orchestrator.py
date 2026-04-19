from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from graph.state import AgentState
from agents.resume_parser import resume_parser_agent
from agents.market_research import market_research_agent
from agents.gap_analyzer import gap_analyzer_agent
from agents.resume_rewriter import resume_rewriter_agent
import json


def self_reflection_node(state: AgentState) -> AgentState:
    """
    Checks quality of all agent outputs.
    Decides if any agent needs to retry.
    """

    print("\n🧠 Orchestrator: Running self reflection...")

    # ← ChatGroq inside function
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    )

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

    Return:
    {{
        "confidence_score": 0.8,
        "quality_issues": [],
        "needs_retry": false,
        "retry_agent": "none",
        "reflection_summary": "one sentence quality verdict"
    }}
    """

    try:
        response = llm.invoke(reflection_prompt)
        raw = response.content.replace("```json", "").replace("```", "").strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        reflection = json.loads(raw[start:end])

        state["confidence_score"] = reflection.get("confidence_score", 0.5)
        state["needs_retry"] = reflection.get("needs_retry", False)
        state["retry_agent"] = reflection.get("retry_agent", "none")

        print(f"   → Confidence Score: {state['confidence_score']}")
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

    gaps = skill_gaps.get("skill_gaps", [])
    critical_gaps = [g for g in gaps if g.get("priority") == "critical"]
    important_gaps = [g for g in gaps if g.get("priority") == "important"]
    hallucination_report = state.get("hallucination_report", [])

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
        "interview_questions": questions[:5],
        "sources": market_skills.get("sources", [])[:5],
        "candidate_summary": skill_gaps.get("candidate_summary", ""),
        "quick_wins": skill_gaps.get("quick_wins", []),
        "hallucinations_found": len(hallucination_report) > 0,
        "hallucination_report": hallucination_report,
        "hallucinations_removed": len(hallucination_report),
    }

    state["final_report"] = report

    print(f"✅ Final report compiled for {report['candidate_name']}")
    print(f"   Match Score: {report['match_score']}%")
    print(f"   ATS: {report['ats_score_before']} → {report['ats_score_after']}")

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
        "hallucination_report": [],
        "confidence_score": 0.0,
        "needs_retry": False,
        "retry_agent": "none",
        "retry_count": 0,
        "final_report": {},
        "messages": []
    }

    app = build_graph()
    final_state = app.invoke(initial_state)

    print("\n" + "="*50)
    print("✅ AGENT PIPELINE COMPLETE")
    print("="*50)

    return final_state["final_report"]
