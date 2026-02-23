"""Research Agent -- autonomous company and role information gathering."""

from __future__ import annotations

import json

from agents.base_agent import BaseAgent
from tools.registry import ToolRegistry


class ResearchAgent(BaseAgent):
    """Autonomous agent that researches a company and role for interview prep.

    Tools: web_search, web_scrape, jd_parser
    """

    name = "ResearchAgent"
    system_prompt = (
        "You are an autonomous Research Agent preparing for a job interview. "
        "Your goal: gather comprehensive information about the target company and role.\n\n"
        "Available tools:\n"
        "- web_search: Search the web for information\n"
        "- web_scrape: Fetch and extract content from a URL (NOT LinkedIn)\n"
        "- jd_parser: Parse job description text into structured data\n\n"
        "Research strategy:\n"
        "1. Search for the official job description\n"
        "2. Scrape the JD page and parse it with jd_parser\n"
        "3. Search for recent company news, products, and announcements\n"
        "4. Search for interview experiences and tips\n"
        "5. Understand the company's competitive landscape\n"
        "6. Extract technical keywords useful for speech recognition\n\n"
        "IMPORTANT: When you have gathered enough information, return your final answer "
        "as a SINGLE JSON object. Do NOT include any text outside the JSON.\n"
        "Return ONLY valid JSON with these keys:\n"
        "- company_profile: {name, description, recent_news, culture, products}\n"
        "- jd_structured: parsed JD output\n"
        "- interview_tips: [tips from reviews]\n"
        "- keywords: [technical keywords for speech recognition]\n"
        "- competitive_landscape: brief competitive analysis string"
    )

    def __init__(self, registry: ToolRegistry, model: str = "haiku"):
        super().__init__(
            registry=registry,
            model=model,
            tool_names=["web_search", "web_scrape", "jd_parser"],
        )

    def research(self, company: str, role: str) -> dict:
        """Run autonomous research loop for a company and role.

        Returns:
            Structured research output dict.
        """
        prompt = (
            f"Research the following for interview preparation:\n"
            f"- Company: {company}\n"
            f"- Role: {role}\n\n"
            "Conduct thorough research using your tools, then return a JSON object."
        )
        response = self.run(prompt, max_turns=15)
        return _parse_json_safe(response)


def _parse_json_safe(text: str) -> dict:
    """Try to parse JSON from agent response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for start_delim, end_delim in [("```json", "```"), ("```", "```")]:
        try:
            start = text.index(start_delim) + len(start_delim)
            end = text.index(end_delim, start)
            return json.loads(text[start:end].strip())
        except (ValueError, json.JSONDecodeError):
            continue
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"raw_response": text}
