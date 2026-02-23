"""Resume Analyst Agent -- resume/LinkedIn analysis and gap detection."""

from __future__ import annotations

import json

from agents.base_agent import BaseAgent
from tools.registry import ToolRegistry


class ResumeAgent(BaseAgent):
    """Analyzes resume, LinkedIn, and other documents against a JD.

    Tools: document_reader, gap_analyzer, web_search
    """

    name = "ResumeAgent"
    system_prompt = (
        "You are a Resume Analyst Agent. Your goal: analyze a candidate's resume and profile, "
        "then compare against job requirements to identify strengths and gaps.\n\n"
        "Available tools:\n"
        "- document_reader: Read and structure a PDF document (resume or LinkedIn)\n"
        "- gap_analyzer: Compare JD requirements against resume to find matches and gaps\n"
        "- web_search: Search for supplementary info (e.g., LinkedIn public profile via Google)\n\n"
        "Analysis strategy:\n"
        "1. Read the resume PDF using document_reader (file_path, document_type='resume')\n"
        "2. If LinkedIn PDF is provided, read it with document_reader (document_type='linkedin')\n"
        "3. If only LinkedIn URL is provided, use web_search with 'site:linkedin.com' query\n"
        "4. Use gap_analyzer to compare JD requirements against the structured resume\n"
        "5. Identify predicted weak points for the interview\n\n"
        "IMPORTANT: When analysis is complete, return your final answer "
        "as a SINGLE JSON object. Do NOT include any text outside the JSON.\n"
        "Return ONLY valid JSON with these keys:\n"
        "- candidate_profile: {name, current_role, experience_years, skills, education, highlights}\n"
        "- gap_analysis: output from gap_analyzer\n"
        "- predicted_weak_points: [topics candidate will struggle with]\n"
        "- talking_points: [strong experiences to highlight in interview]\n"
        "- additional_context: any LinkedIn or GitHub insights"
    )

    def __init__(self, registry: ToolRegistry, model: str = "haiku"):
        super().__init__(
            registry=registry,
            model=model,
            tool_names=["document_reader", "gap_analyzer", "web_search"],
        )

    def analyze(
        self,
        resume_path: str,
        jd_structured: dict,
        linkedin_path: str | None = None,
        linkedin_url: str | None = None,
        github_url: str | None = None,
    ) -> dict:
        """Analyze resume and supplementary documents against JD.

        Returns:
            Structured analysis output dict.
        """
        parts = [
            f"Analyze this candidate for the following job:\n\n",
            f"JD Requirements:\n{json.dumps(jd_structured, ensure_ascii=False)}\n\n",
            f"Resume PDF path: {resume_path}\n",
        ]

        if linkedin_path:
            parts.append(f"LinkedIn PDF path: {linkedin_path}\n")
        if linkedin_url:
            parts.append(
                f"LinkedIn URL: {linkedin_url}\n"
                "(Use web_search with 'site:linkedin.com' to find public info. "
                "Do NOT scrape LinkedIn directly.)\n"
            )
        if github_url:
            parts.append(f"GitHub URL: {github_url}\n")

        parts.append(
            "\nSteps:\n"
            "1. Read the resume using document_reader with the file_path and document_type='resume'\n"
            "2. Read LinkedIn if available\n"
            "3. Run gap_analyzer with jd_structured and the structured resume\n"
            "4. Return your final JSON analysis"
        )

        prompt = "".join(parts)
        response = self.run(prompt, max_turns=10)
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
