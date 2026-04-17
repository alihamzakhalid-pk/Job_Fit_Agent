from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from graph.state import AgentState
from tools.search_tool import tavily_search
from tools.retry_utils import llm_retry_decorator
from config import (
    LLM_MODEL,
    LLM_TEMPERATURE_PARSING,
    LLM_TIMEOUT,
    SEARCH_RESULTS_PER_QUERY,
    SEARCH_QUERIES_COUNT,
    MAX_MARKET_SKILLS,
    SEARCH_RESULTS_MAX_CHARS,
)
import json

# Initialize LLM once at module level
llm = ChatGroq(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE_PARSING,
    timeout=LLM_TIMEOUT,
)

SKILL_EXTRACTOR_PROMPT = """
You are a job market analyst.
Below are search results about skills required for a {job_role} position.
Extract ALL specific technical skills, tools, and technologies mentioned.
Return ONLY a valid JSON object. No explanation. No extra text.

Search Results:
{search_results}

Return this exact structure:
{{
    "skills": [
        {{
            "name": "skill name",
            "frequency": 1,
            "category": "one of: language/framework/tool/cloud/database/concept",
            "importance": "one of: critical/important/good_to_have"
        }}
    ],
    "job_role_detected": "{job_role}",
    "market_summary": "2 sentence summary of what market wants"
}}
"""

prompt = PromptTemplate(
    template=SKILL_EXTRACTOR_PROMPT,
    input_variables=["job_role", "search_results"]
)


def build_search_queries(job_role: str) -> list:
    return [
        f"most demanded skills {job_role} jobs 2026",
        f"top companies hiring {job_role} required technical skills",
        f"{job_role} job description must have skills salary 2026"
    ]


def extract_job_role(state: AgentState) -> str:
    job_description = state["job_description"]
    extract_prompt = f"""
    From this job description, extract ONLY the job title/role in 2-4 words.
    Return only the job title, nothing else.
    
    Job Description:
    {job_description[:500]}
    
    Job Title:
    """
    response = llm.invoke(extract_prompt)
    job_role = response.content.strip().replace('"', '').replace("'", "").strip()
    return job_role


def combine_search_results(all_results: list) -> str:
    seen_urls = set()
    combined = []

    for results in all_results:
        for result in results:
            url = result.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                combined.append(
                    f"Title: {result['title']}\n"
                    f"Content: {result['content'][:300]}\n"
                    f"Source: {result['url']}\n"
                )

    return "\n---\n".join(combined)


def clean_and_parse_json(raw_output: str) -> dict:
    raw_output = raw_output.replace("```json", "").replace("```", "").strip()
    start = raw_output.find("{")
    end = raw_output.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON in output")
    return json.loads(raw_output[start:end])


def market_research_agent(state: AgentState) -> AgentState:
    """
    Agent 2: Researches current market skill demand.
    Reads from state:  job_description
    Writes to state:   market_skills
    """

    print("\n🌐 Agent 2: Researching market skills...")

    try:
        print("   → Detecting job role...")
        job_role = extract_job_role(state)
        print(f"   → Job role detected: {job_role}")

        queries = build_search_queries(job_role)
        print(f"   → Running {len(queries)} market searches...")

        all_results = []
        sources = []

        for i, query in enumerate(queries):
            print(f"   → Search {i+1}: '{query}'")
            results = tavily_search(query, max_results=SEARCH_RESULTS_PER_QUERY) or []
            all_results.append(results)
            for r in results:
                if r.get("url"):
                    sources.append(r["url"])

        combined_text = combine_search_results(all_results)

        print("   → Analyzing market data with LLM...")
        @llm_retry_decorator
        def analyze_market_with_retry():
            chain = prompt | llm
            return chain.invoke({
                "job_role": job_role,
                "search_results": combined_text[:SEARCH_RESULTS_MAX_CHARS]
            })
        
        response = analyze_market_with_retry()
        market_data = clean_and_parse_json(response.content)

        skills = market_data.get("skills", [])
        skills_sorted = sorted(
            skills,
            key=lambda x: x.get("frequency", 0),
            reverse=True
        )

        market_data["skills"] = skills_sorted
        market_data["sources"] = list(set(sources))[:10]

        state["market_skills"] = market_data

        print(f"✅ Agent 2: Found {len(skills_sorted)} market skills")
        print(f"   Top 3: {[s['name'] for s in skills_sorted[:3]]}")

    except Exception as e:
        print(f"❌ Agent 2 Error: {e}")
        state["market_skills"] = {"skills": [], "sources": []}

    return state
