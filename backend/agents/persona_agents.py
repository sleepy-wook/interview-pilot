"""Persona Agents -- Hiring Manager, Technical Lead, HR interviewer personas."""

from __future__ import annotations

import json

from agents.base_agent import BaseAgent
from tools.registry import ToolRegistry


class PersonaAgent(BaseAgent):
    """Base class for interview persona agents.

    Each persona has:
    - Unique personality and question style (system_prompt)
    - Independent Q&A memory
    - Cross-persona observation log
    - Optional tool access
    """

    persona_type: str = ""

    def __init__(self, registry: ToolRegistry, model: str = "haiku", tool_names: list[str] | None = None):
        super().__init__(registry=registry, model=model, tool_names=tool_names)
        self.qa_memory: list[dict] = []
        self.observations: list[dict] = []

    def record_qa(self, question: str, answer: str, analysis: dict) -> None:
        """Record a Q&A turn from this persona."""
        self.qa_memory.append({
            "question": question,
            "answer": answer,
            "quality": analysis.get("quality", "unknown"),
            "flags": analysis.get("flags", []),
        })

    def observe(self, persona_type: str, question: str, answer: str) -> None:
        """Record observation from another persona's Q&A."""
        self.observations.append({
            "persona": persona_type,
            "question": question,
            "answer_summary": answer[:200],
        })

    def get_memory_summary(self) -> str:
        """Get summary of this persona's Q&A history."""
        if not self.qa_memory:
            return "No questions asked yet."
        lines = []
        for i, qa in enumerate(self.qa_memory, 1):
            lines.append(f"Q{i} ({qa['quality']}): {qa['question'][:80]}")
        return "\n".join(lines)

    def generate_follow_up(
        self,
        last_question: str,
        last_answer: str,
        analysis: dict,
        research_context: dict | None = None,
    ) -> str:
        """Generate a follow-up question in this persona's style."""
        context_str = json.dumps(research_context, ensure_ascii=False)[:800] if research_context else "None"
        missing = analysis.get("missing_points", [])
        flags = analysis.get("flags", [])
        quality = analysis.get("quality", "weak")

        # Truncate answer to key parts for the prompt
        answer_snippet = last_answer[:500]

        prompt = (
            f"CONTEXT (do NOT repeat this in your question):\n"
            f"Previous question topic: \"{last_question[:100]}\"\n"
            f"Candidate's answer ({quality}): \"{answer_snippet}\"\n"
            f"Missing points: {missing}\n"
            f"Flags: {flags}\n"
            f"Candidate background: {context_str}\n\n"
            "TASK: Generate ONE follow-up question.\n\n"
            "CRITICAL RULES:\n"
            "- Start by referencing something FROM THE CANDIDATE'S ANSWER, not from the original question\n"
            "- Do NOT reuse or paraphrase the opening of the previous question\n"
            "- Pick a specific claim, detail, or gap from their answer and dig into it\n"
            "- Push for concrete examples, numbers, or specifics they didn't provide\n"
            "- Keep it short: one sentence, max two\n"
            "- Sound like a real interviewer reacting to what they just heard\n\n"
            "GOOD examples:\n"
            "- 'You mentioned a 0.85 confidence threshold -- how did you arrive at that number?'\n"
            "- 'Interesting that you routed borderline cases to human review. What was the volume like?'\n"
            "- 'You talked about the validation pipeline, but what happened when it disagreed with the OCR output?'\n\n"
            "BAD examples (never do this):\n"
            "- 'You mentioned building a RAG pipeline. Walk me through...' (repeats original question framing)\n"
            "- 'Tell me more about your project.' (too generic)\n\n"
            "Return ONLY the question text, nothing else."
        )
        self.reset_memory()
        return self.run(prompt, max_turns=3)


class HMPersona(PersonaAgent):
    """Hiring Manager persona -- business fit, culture, leadership."""

    persona_type = "HM"
    system_prompt = (
        "You are a Hiring Manager interviewer.\n"
        "Personality: Warm but sharp. You start friendly to make the candidate comfortable, "
        "then ask the real question. You focus on business fit, culture alignment, and leadership.\n\n"
        "Question style examples:\n"
        "- 'Why do you want to move from manufacturing to SaaS?'\n"
        "- 'How would you handle a customer making technically incorrect demands?'\n"
        "- 'Tell me what you know about our company.'\n"
        "- 'Describe a time you dealt with team conflict.'\n\n"
        "When generating follow-ups, push gently but firmly on vague answers."
    )

    def __init__(self, registry: ToolRegistry, model: str = "haiku"):
        super().__init__(registry=registry, model=model, tool_names=None)


class TechPersona(PersonaAgent):
    """Technical Lead persona -- technical depth, architecture, problem solving."""

    persona_type = "Tech"
    system_prompt = (
        "You are a Technical Lead interviewer.\n"
        "Personality: Dry and precise. No fluff. If the answer is vague, "
        "say 'Can you be more specific?'. You focus on technical depth, "
        "architecture understanding, and problem-solving ability.\n\n"
        "Question style examples:\n"
        "- 'Explain how Delta Lake implements ACID transactions.'\n"
        "- 'Why is Spark's shuffle operation expensive?'\n"
        "- 'Walk me through the architecture of your project.'\n"
        "- 'How would you approach processing 100TB of data?'\n\n"
        "You can use web_scrape to check GitHub repos mentioned by candidates, "
        "and web_search to fact-check technical claims."
    )

    def __init__(self, registry: ToolRegistry, model: str = "haiku"):
        super().__init__(registry=registry, model=model, tool_names=["web_scrape", "web_search"])


class HRPersona(PersonaAgent):
    """HR persona -- soft skills, motivation, culture fit, expectations."""

    persona_type = "HR"
    system_prompt = (
        "You are an HR interviewer.\n"
        "Personality: Friendly and empathetic, but persistent. "
        "If the candidate is vague about motivations, dig deeper. "
        "You focus on soft skills, career goals, and realistic expectations.\n\n"
        "Question style examples:\n"
        "- 'Where do you see yourself in five years?'\n"
        "- 'What are your salary expectations?'\n"
        "- 'What was the most challenging moment at your previous job?'\n"
        "- 'Do you prefer remote work or working from the office?'\n\n"
        "You can use web_search to look up market salary data when relevant."
    )

    def __init__(self, registry: ToolRegistry, model: str = "haiku"):
        super().__init__(registry=registry, model=model, tool_names=["web_search"])
