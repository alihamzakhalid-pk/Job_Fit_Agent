from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from graph.state import AgentState
from config import LLM_MODEL, LLM_TEMPERATURE_PARSING, LLM_TIMEOUT
from tools.retry_utils import llm_retry_decorator
import json

# Initialize LLM once at module level
llm = ChatGroq(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE_PARSING,
    timeout=LLM_TIMEOUT,
)

RESUME_PARSER_PROMPT = """
You are an expert resume parser. 
Extract all information from this resume and return ONLY a valid JSON object.
No explanation. No extra text. Just JSON.

Resume Text:
{resume_text}

Return this exact JSON structure:
{{
    "personal_info": {{
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": ""
    }},
    "skills": {{
        "technical": [],
        "soft": [],
        "tools": [],
        "languages": []
    }},
    "experience": [
        {{
            "company": "",
            "role": "",
            "duration": "",
            "responsibilities": [],
            "achievements": []
        }}
    ],
    "education": [
        {{
            "institution": "",
            "degree": "",
            "field": "",
            "year": "",
            "gpa": ""
        }}
    ],
    "projects": [
        {{
            "name": "",
            "description": "",
            "technologies": [],
            "impact": ""
        }}
    ],
    "certifications": []
}}
"""

prompt = PromptTemplate(
    template=RESUME_PARSER_PROMPT,
    input_variables=["resume_text"]
)


def resume_parser_agent(state: AgentState) -> AgentState:
    """
    Agent 1: Parses resume text into structured JSON.
    Reads from state: resume_text
    Writes to state: parsed_resume
    """

    print("🔍 Agent 1: Parsing resume...")

    resume_text = state["resume_text"]

    if not resume_text:
        print("❌ No resume text found in state")
        state["parsed_resume"] = {}
        return state

    try:
        @llm_retry_decorator
        def parse_resume_with_retry():
            chain = prompt | llm
            return chain.invoke({"resume_text": resume_text})
        
        response = parse_resume_with_retry()
        raw_output = response.content
        parsed_resume = clean_and_parse_json(raw_output)
        state["parsed_resume"] = parsed_resume

        print("✅ Agent 1: Resume parsed successfully")
        print(f"   Found {len(parsed_resume.get('skills', {}).get('technical', []))} technical skills")
        print(f"   Found {len(parsed_resume.get('experience', []))} work experiences")
        print(f"   Found {len(parsed_resume.get('projects', []))} projects")

    except Exception as e:
        print(f"❌ Agent 1 Error: {e}")
        state["parsed_resume"] = {}

    return state


def clean_and_parse_json(raw_output: str) -> dict:
    """
    Safely cleans and parses JSON from LLM output.
    """
    raw_output = raw_output.replace("```json", "").replace("```", "")
    raw_output = raw_output.strip()

    start = raw_output.find("{")
    end = raw_output.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("No JSON found in LLM output")

    json_str = raw_output[start:end]
    return json.loads(json_str)
