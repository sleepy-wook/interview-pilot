"""Master Agent -- interview strategy planning and real-time orchestration."""

from __future__ import annotations

import json
import random

from agents.base_agent import BaseAgent
from agents.persona_agents import PersonaAgent
from core.state import InterviewState, TurnRecord
from tools.registry import ToolRegistry


class MasterAgent(BaseAgent):
    """The conductor of the interview.

    Phase 1: Generate interview plan from Research Brief.
    Phase 2: Real-time orchestration loop -- route questions to Personas,
             analyze answers, detect inconsistencies, decide next action.
    """

    name = "MasterAgent"
    system_prompt = (
        "You are the Master Agent orchestrating a mock interview. "
        "You do NOT ask questions directly. You plan the interview strategy, "
        "decide which Persona (HM, Tech, HR) should ask the next question, "
        "and analyze answers to determine the best next action.\n\n"
        "Available actions:\n"
        "- Route to a Persona for the next question\n"
        "- Request a follow-up from the same Persona\n"
        "- Generate a dynamic question based on detected gaps\n"
        "- Flag inconsistencies for cross-check\n"
        "- End the interview when coverage is sufficient"
    )

    def __init__(
        self,
        registry: ToolRegistry,
        state: InterviewState,
        personas: dict[str, PersonaAgent] | None = None,
    ):
        tool_names = [
            "question_generator",
            "hint_generator",
            "answer_analyzer",
            "consistency_checker",
            "persona_router",
        ]
        model = state.model if state else "haiku"
        super().__init__(registry=registry, model=model, tool_names=tool_names)
        self.state = state
        self.personas = personas or {}

    # ── Phase 1: Plan Generation ──

    def generate_plan(self) -> list[dict]:
        """Generate interview plan from Research Brief.

        Uses a direct LLM call (no tools) since plan generation
        doesn't require tool use -- just structured output.

        Returns:
            List of planned questions with persona assignments.
        """
        brief_str = json.dumps(self.state.research_brief, ensure_ascii=False)
        if len(brief_str) > 6000:
            brief_str = brief_str[:6000] + "..."

        # Extract candidate-specific context for personalized questions
        candidate = self.state.research_brief.get("candidate_profile", {})
        gaps = self.state.research_brief.get("gap_analysis", {})
        weak_points = self.state.research_brief.get("predicted_weak_points", [])

        candidate_section = ""
        if candidate:
            candidate_section = (
                "\n\nCANDIDATE PROFILE (use this to personalize questions):\n"
                f"- Name: {candidate.get('name', 'Unknown')}\n"
                f"- Current role: {candidate.get('current_role', 'N/A')}\n"
                f"- Experience: {candidate.get('experience_years', 'N/A')} years\n"
                f"- Skills: {', '.join(candidate.get('skills', [])[:10])}\n"
                f"- Education: {candidate.get('education', 'N/A')}\n"
            )

        gaps_section = ""
        gap_items = gaps.get("gaps", []) if isinstance(gaps, dict) else []
        if gap_items:
            gaps_section = "\n\nIDENTIFIED GAPS (probe these with specific questions):\n"
            for g in gap_items[:5]:
                if isinstance(g, dict):
                    gaps_section += f"- {g.get('requirement', '')} (severity: {g.get('severity', 'moderate')})\n"

        weak_section = ""
        if weak_points:
            weak_section = "\n\nPREDICTED WEAK POINTS (create questions targeting these):\n"
            for wp in weak_points[:5]:
                weak_section += f"- {wp}\n"

        system = (
            "You are an interview strategist. Generate a structured interview plan "
            "that is PERSONALIZED to the specific candidate. "
            "Return ONLY a valid JSON array, no other text."
        )
        prompt = (
            f"Create an interview plan for a {self.state.role} position at {self.state.company}.\n\n"
            f"Research Brief:\n{brief_str}\n"
            f"{candidate_section}{gaps_section}{weak_section}\n"
            f"Generate exactly {self.state.question_count} questions. For each, provide:\n"
            "- question: a SPECIFIC interview question that references the candidate's actual background\n"
            "- persona: HM, Tech, or HR\n"
            "- topic: the topic category\n"
            "- priority: high, medium, or low\n"
            "- depth: surface, moderate, or deep\n\n"
            "CRITICAL RULES:\n"
            "1. At least 30% of questions MUST reference the candidate's specific resume, projects, or experience.\n"
            "2. Questions about gaps should mention the gap and ask the candidate to address it.\n"
            "3. Do NOT generate generic questions like 'Tell me about yourself'. Instead, reference specifics like "
            "'I see you worked on X at Y -- can you walk me through the architecture?'\n"
            "4. For technical questions, reference specific technologies from the candidate's background.\n"
            "5. Balance across personas. Start with HM for rapport, alternate personas, put HR toward the end.\n"
            "Return ONLY a JSON array."
        )
        text, _ = self.llm.converse(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=4096,
            temperature=0.5,
        )
        self.state.interview_plan = self._parse_plan(text)

        # Build coverage tracking
        self.state.coverage = {
            "covered": [],
            "remaining": [q.get("topic", "") for q in self.state.interview_plan],
        }

        return self.state.interview_plan

    # ── Phase 2: Interview Loop ──

    def _maybe_generate_ice_breaker(self) -> dict | None:
        """Optionally generate a casual ice-breaker question (60% chance)."""
        if random.random() > 0.6:
            return None  # Skip ice breaker this time

        candidate = self.state.research_brief.get("candidate_profile", {})
        candidate_name = candidate.get("name", "")
        candidate_role = candidate.get("current_role", "")

        context_hint = ""
        if candidate_name:
            context_hint += f"The candidate's name is {candidate_name}. "
        if candidate_role:
            context_hint += f"They currently work as {candidate_role}. "

        system = (
            "You are a warm, friendly Hiring Manager starting an interview. "
            "Generate ONE casual ice-breaker to put the candidate at ease. "
            "Keep it short and natural. Return ONLY the question text."
        )
        prompt = (
            f"Generate a brief, friendly ice-breaker for a {self.state.role} "
            f"interview at {self.state.company}.\n"
            f"{context_hint}\n"
            "Examples: 'How are you doing today?', 'Thanks for taking the time to chat with us!', "
            "'How's your day going so far?'\n"
            "Return ONLY the ice-breaker text."
        )
        text, _ = self.llm.converse(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=200,
            temperature=0.8,
        )
        question_text = text.strip().strip('"')

        return {
            "question": question_text,
            "persona": "HM",
            "topic": "ice_breaker",
            "hints": {},
            "rationale": "Ice breaker to warm up",
            "follow_up_if_weak": "",
        }

    def get_next_question(self) -> dict | None:
        """Get the next question + hints for the interview.

        Returns:
            Dict with question, persona, topic, hints, etc. None if interview is over.
        """
        # Ice breaker before first real question
        if self.state.current_index == 0 and not self.state.ice_breaker_done:
            self.state.ice_breaker_done = True
            ice_breaker = self._maybe_generate_ice_breaker()
            if ice_breaker:
                return ice_breaker

        # Check if we should use a dynamic question (follow-up)
        if self.state.dynamic_questions:
            plan_item = self.state.dynamic_questions.pop(0)
            self._last_from_plan = False
        elif self.state.current_index < len(self.state.interview_plan):
            plan_item = self.state.interview_plan[self.state.current_index]
            self._last_from_plan = True
        else:
            return None  # Interview is over

        persona = plan_item.get("persona", "HM")
        topic = plan_item.get("topic", "general")
        depth = plan_item.get("depth", "moderate")

        # Generate question via question_generator tool
        question_result = _safe_json(self.registry.execute("question_generator", {
            "topic": topic,
            "persona": persona,
            "depth": depth,
            "history_summary": self._get_history_summary(),
            "research_brief_context": _truncate_dict(self.state.research_brief, 3000),
        }))

        question_text = question_result.get("question", plan_item.get("question", ""))

        # Generate hints via hint_generator tool
        hint_result = _safe_json(self.registry.execute("hint_generator", {
            "question": question_text,
            "persona": persona,
            "resume_context": _truncate_dict(
                self.state.research_brief.get("candidate_profile", {}), 1000
            ),
            "research_brief_context": _truncate_dict(self.state.research_brief, 1000),
        }))

        return {
            "question": question_text,
            "persona": persona,
            "topic": topic,
            "hints": hint_result,
            "rationale": question_result.get("rationale", ""),
            "follow_up_if_weak": question_result.get("follow_up_if_weak", ""),
        }

    def process_answer(self, question: str, answer: str, persona: str) -> dict:
        """Process user's answer: analyze, check consistency, route next.

        Returns:
            Dict with analysis, consistency, routing, and turn record.
        """
        # Ice breaker: lightweight path — skip analysis/routing, don't advance plan
        if self._is_ice_breaker_answer():
            turn = TurnRecord(
                turn_number=len(self.state.answer_history) + 1,
                persona=persona,
                question=question,
                answer=answer,
                answer_analysis={"quality": "n/a", "confidence_score": 0,
                                 "specificity_score": 0, "star_score": 0},
            )
            self.state.answer_history.append(turn)
            return {
                "analysis": turn.answer_analysis,
                "consistency": None,
                "routing": {"action": "next_planned", "next_persona": "HM",
                            "reason": "ice breaker done"},
                "turn": turn,
            }

        # 1. Analyze answer
        analysis = _safe_json(self.registry.execute("answer_analyzer", {
            "question": question,
            "answer": answer,
            "persona": persona,
        }))

        # 2. Create turn record and update state
        turn = TurnRecord(
            turn_number=len(self.state.answer_history) + 1,
            persona=persona,
            question=question,
            answer=answer,
            answer_analysis=analysis,
        )
        self.state.answer_history.append(turn)

        # 3. Update persona memory
        if persona in self.personas:
            self.personas[persona].record_qa(question, answer, analysis)
            # Other personas observe
            for p_type, p_agent in self.personas.items():
                if p_type != persona:
                    p_agent.observe(persona, question, answer)

        # 4. Update coverage
        current_plan = (
            self.state.interview_plan[self.state.current_index]
            if self.state.current_index < len(self.state.interview_plan)
            else {}
        )
        topic = current_plan.get("topic", "")
        if topic and topic in self.state.coverage.get("remaining", []):
            self.state.coverage["remaining"].remove(topic)
            self.state.coverage["covered"].append(topic)

        # 5. Check consistency if enough history (3+ turns)
        consistency = None
        if len(self.state.answer_history) >= 3:
            answers_for_check = [
                {"question": t.question, "answer": t.answer, "persona": t.persona}
                for t in self.state.answer_history
            ]
            consistency = _safe_json(self.registry.execute("consistency_checker", {
                "answers": answers_for_check,
            }))
            if consistency and not consistency.get("consistent", True):
                for c in consistency.get("contradictions", []):
                    flag = f"inconsistency: {c.get('description', '')[:100]}"
                    if flag not in self.state.flags:
                        self.state.flags.append(flag)

        # 6. Add flags from answer analysis
        for flag in analysis.get("flags", []):
            flag_str = f"{persona}_{topic}: {flag}"
            if flag_str not in self.state.flags:
                self.state.flags.append(flag_str)

        # 7. Route to next action
        remaining_topics = [
            p.get("topic", "")
            for p in self.state.interview_plan[self.state.current_index + 1:]
        ]
        quality = analysis.get("quality", "adequate")
        answer_summary = answer[:200] if answer else ""
        routing = _safe_json(self.registry.execute("persona_router", {
            "current_persona": persona,
            "answer_quality": quality,
            "remaining_topics": remaining_topics[:5],
            "flags": self.state.flags[-5:],
            "answer_summary": answer_summary,
        }))

        # 8. Handle routing decisions
        action = routing.get("action", "next_planned")
        from_plan = getattr(self, "_last_from_plan", True)

        # Deterministic override: force follow-up for weak/evasive answers
        if quality in ("weak", "evasive") and action == "next_planned":
            action = "follow_up"
            routing["action"] = "follow_up"
            routing["reason"] = f"Forced follow-up: answer quality was {quality}"

        # Allow follow-ups from both planned and dynamic questions,
        # but limit chain depth to prevent infinite loops (max 2 consecutive)
        chain_depth = 0
        if not from_plan:
            chain_depth = 1  # current question was already a follow-up
            # Count consecutive non-plan questions before this one
            for prev in reversed(self.state.answer_history[:-1]):
                if "(follow-up)" in prev.question or not from_plan:
                    chain_depth += 1
                else:
                    break
        max_chain_depth = 2
        if action == "follow_up" and persona in self.personas and chain_depth < max_chain_depth:
            follow_up_q = self.personas[persona].generate_follow_up(
                question, answer, analysis,
                self.state.research_brief,
            )
            self.state.dynamic_questions.insert(0, {
                "question": follow_up_q,
                "persona": persona,
                "topic": topic.replace(" (follow-up)", "") + " (follow-up)",
                "depth": "deep",
                "priority": "high",
            })
        elif action == "dynamic_question":
            self.state.dynamic_questions.append({
                "persona": routing.get("next_persona", persona),
                "topic": routing.get("suggested_topic", "general"),
                "depth": "moderate",
                "priority": "high",
            })

        # 9. Advance plan index only when a planned question was asked
        if from_plan:
            self.state.current_index += 1

        return {
            "analysis": analysis,
            "consistency": consistency,
            "routing": routing,
            "turn": turn,
        }

    def should_end_interview(self) -> bool:
        """Check if the interview should end."""
        # End if plan is exhausted and no dynamic questions
        if (self.state.current_index >= len(self.state.interview_plan)
                and not self.state.dynamic_questions):
            return True
        return False

    # ── Helpers ──

    def _is_ice_breaker_answer(self) -> bool:
        """Check if the current answer is for an ice-breaker question."""
        # Ice breaker is always the first question, and we haven't advanced the plan
        return (
            len(self.state.answer_history) == 0
            and self.state.ice_breaker_done
            and self.state.current_index == 0
        )

    def _get_history_summary(self) -> str:
        """Get concise summary of answer history for context."""
        if not self.state.answer_history:
            return "No questions asked yet."
        lines = []
        for t in self.state.answer_history[-5:]:  # Last 5 turns
            quality = t.answer_analysis.get("quality", "?")
            lines.append(f"[{t.persona}] {t.question[:60]}... -> {quality}")
        return "\n".join(lines)

    @staticmethod
    def _parse_plan(response: str) -> list[dict]:
        """Try to parse JSON plan from LLM response."""
        try:
            start = response.index("[")
            end = response.rindex("]") + 1
            return json.loads(response[start:end])
        except (ValueError, json.JSONDecodeError):
            return []


def _safe_json(text: str) -> dict:
    """Parse JSON from tool output, returning empty dict on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"raw": text}


def _truncate_dict(d: dict, max_chars: int) -> dict:
    """Truncate a dict's JSON representation for LLM context limits."""
    s = json.dumps(d, ensure_ascii=False)
    if len(s) <= max_chars:
        return d
    try:
        return json.loads(s[:max_chars - 3] + "}")
    except json.JSONDecodeError:
        return {}
