"""Agent module -- Research, Resume, Persona, Master, and Evaluation agents."""

from agents.research_agent import ResearchAgent
from agents.resume_agent import ResumeAgent
from agents.persona_agents import HMPersona, TechPersona, HRPersona
from agents.master_agent import MasterAgent


def merge_research_brief(research_output: dict, resume_output: dict) -> dict:
    """Merge Research Agent and Resume Agent outputs into a unified Research Brief.

    This Research Brief is used by MasterAgent to plan the interview.
    """
    return {
        "company_profile": research_output.get("company_profile", {}),
        "jd_structured": research_output.get("jd_structured", {}),
        "candidate_profile": resume_output.get("candidate_profile", {}),
        "gap_analysis": resume_output.get("gap_analysis", {}),
        "interview_tips": research_output.get("interview_tips", []),
        "predicted_weak_points": resume_output.get("predicted_weak_points", []),
        "talking_points": resume_output.get("talking_points", []),
        "keywords": research_output.get("keywords", []),
        "competitive_landscape": research_output.get("competitive_landscape", ""),
    }


__all__ = [
    "ResearchAgent", "ResumeAgent",
    "HMPersona", "TechPersona", "HRPersona",
    "MasterAgent",
    "merge_research_brief",
]
