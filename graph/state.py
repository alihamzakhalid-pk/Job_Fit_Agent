from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    # INPUT
    resume_text: str
    job_description: str

    # AGENT 1 OUTPUT
    parsed_resume: dict

    # AGENT 2 OUTPUT
    market_skills: dict

    # AGENT 3 OUTPUT
    skill_gaps: dict
    match_score: float

    # AGENT 4 OUTPUT
    rewritten_bullets: dict
    ats_score_before: int
    ats_score_after: int
    interview_questions: list

    # ORCHESTRATOR
    confidence_score: float
    needs_retry: bool
    retry_agent: str
    retry_count: int
    final_report: dict

    # MEMORY
    messages: List[dict]
