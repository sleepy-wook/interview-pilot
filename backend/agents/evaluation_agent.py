"""Evaluation Agent -- post-interview analysis, scoring, and report generation.

Phase 3: Takes the full interview state and produces:
- Per-question detailed evaluation (quality, STAR, specificity)
- Comprehensive scorecard with persona scores
- Hint usage analysis
- Voice metrics summary
- Improved model answers for weak answers
- Action plan for next interview
"""

from __future__ import annotations

import json

from agents.base_agent import BaseAgent
from core.state import InterviewState
from tools.registry import ToolRegistry


class EvaluationAgent(BaseAgent):
    """Post-interview evaluation and report generation.

    Unlike other agents, this one uses a direct tool-calling approach
    (not agentic loop) since the evaluation pipeline is deterministic:
    1. Run star_detector on each answer
    2. Run consistency_checker on all answers
    3. Run answer_improver on weak answers
    4. Generate scorecard and action plan via LLM
    """

    name = "EvaluationAgent"
    system_prompt = (
        "You are an expert interview evaluator. Analyze interview performance "
        "objectively and provide actionable feedback."
    )

    def __init__(self, registry: ToolRegistry, model: str = "haiku"):
        tool_names = ["star_detector", "consistency_checker", "answer_improver"]
        super().__init__(registry=registry, model=model, tool_names=tool_names)

    def evaluate(self, state: InterviewState) -> dict:
        """Run the full evaluation pipeline.

        Args:
            state: Completed InterviewState with answer_history populated.

        Returns:
            Complete evaluation report dict.
        """
        history = state.answer_history
        if not history:
            return {"error": "No answers to evaluate"}

        # 1. Per-question evaluation with STAR detection
        per_question = self._evaluate_per_question(history, state)

        # 2. Consistency check across all answers
        consistency = self._check_consistency(history)

        # 3. Generate improved answers for weak questions
        model_answers = self._generate_model_answers(history, state)

        # 4. Hint usage analysis
        hint_analysis = self._analyze_hints(history, state)

        # 5. Voice metrics summary
        voice_summary = self._summarize_voice_metrics(history)

        # 6. Generate scorecard and action plan via LLM
        scorecard = self._generate_scorecard(
            per_question, consistency, hint_analysis, voice_summary, state
        )

        return {
            "overall_score": scorecard.get("overall_score", 0),
            "persona_scores": scorecard.get("persona_scores", {}),
            "strengths": scorecard.get("strengths", []),
            "weaknesses": scorecard.get("weaknesses", []),
            "per_question": per_question,
            "consistency": consistency,
            "hint_analysis": hint_analysis,
            "voice_summary": voice_summary,
            "model_answers": model_answers,
            "action_plan": scorecard.get("action_plan", []),
        }

    def _evaluate_per_question(
        self, history: list, state: InterviewState
    ) -> list[dict]:
        """Run star_detector + combine with existing answer_analysis."""
        results = []
        for turn in history:
            # Run STAR detection
            star_result = _safe_json(
                self.registry.execute("star_detector", {"answer": turn.answer})
            )

            results.append({
                "turn_number": turn.turn_number,
                "persona": turn.persona,
                "question": turn.question,
                "answer_preview": turn.answer[:200] + ("..." if len(turn.answer) > 200 else ""),
                "quality": turn.answer_analysis.get("quality", "unknown"),
                "confidence_score": turn.answer_analysis.get("confidence_score", 0),
                "specificity_score": turn.answer_analysis.get("specificity_score", 0),
                "star": {
                    "score": star_result.get("score", 0),
                    "situation": star_result.get("situation", {}).get("present", False),
                    "task": star_result.get("task", {}).get("present", False),
                    "action": star_result.get("action", {}).get("present", False),
                    "result": star_result.get("result", {}).get("present", False),
                    "feedback": star_result.get("feedback", ""),
                },
                "flags": turn.answer_analysis.get("flags", []),
                "hint_used": turn.hint_used,
            })
        return results

    def _check_consistency(self, history: list) -> dict:
        """Run consistency_checker on all answers."""
        if len(history) < 2:
            return {"consistent": True, "contradictions": [], "concerns": []}

        answers_data = [
            {
                "question": turn.question,
                "answer": turn.answer,
                "persona": turn.persona,
            }
            for turn in history
        ]
        return _safe_json(
            self.registry.execute("consistency_checker", {"answers": answers_data})
        )

    def _generate_model_answers(
        self, history: list, state: InterviewState
    ) -> list[dict]:
        """Generate improved answers for weak/adequate questions."""
        model_answers = []
        context = _truncate_dict(state.research_brief, 2000)

        for turn in history:
            quality = turn.answer_analysis.get("quality", "adequate")
            # Generate model answers for weak and adequate answers
            if quality in ("weak", "evasive", "adequate"):
                improved = _safe_json(
                    self.registry.execute("answer_improver", {
                        "question": turn.question,
                        "user_answer": turn.answer,
                        "context": context,
                    })
                )
                model_answers.append({
                    "turn_number": turn.turn_number,
                    "question": turn.question,
                    "original_quality": quality,
                    "improved_answer": improved.get("improved_answer", ""),
                    "reasoning": improved.get("reasoning", []),
                    "tips": improved.get("tips", []),
                    "score_before": improved.get("score_before", 0),
                    "score_after": improved.get("score_after", 0),
                })
        return model_answers

    def _analyze_hints(self, history: list, state: InterviewState) -> dict:
        """Analyze hint usage patterns."""
        total = len(history)
        hints_used = sum(1 for t in history if t.hint_used)
        no_hint_needed = sum(
            1 for t in history
            if not t.hint_used
            and t.answer_analysis.get("quality") in ("strong", "adequate")
        )
        hint_used_well = sum(
            1 for t in history
            if t.hint_used
            and t.answer_analysis.get("quality") in ("strong", "adequate")
        )
        hint_used_still_weak = sum(
            1 for t in history
            if t.hint_used
            and t.answer_analysis.get("quality") in ("weak", "evasive")
        )

        # Topics where hints were used but answer was still weak -> focus areas
        focus_topics = []
        for turn in history:
            if (
                turn.hint_used
                and turn.answer_analysis.get("quality") in ("weak", "evasive")
            ):
                # Find the topic from the plan
                topic = "general"
                if turn.turn_number <= len(state.interview_plan):
                    topic = state.interview_plan[turn.turn_number - 1].get(
                        "topic", "general"
                    )
                focus_topics.append(topic)

        return {
            "total_questions": total,
            "hints_used": hints_used,
            "hints_not_used": total - hints_used,
            "breakdown": {
                "no_hint_needed": no_hint_needed,
                "hint_used_answered_well": hint_used_well,
                "hint_used_still_weak": hint_used_still_weak,
            },
            "hint_usage_rate": round(hints_used / total * 100, 1) if total > 0 else 0,
            "focus_topics": focus_topics,
        }

    def _summarize_voice_metrics(self, history: list) -> dict:
        """Aggregate voice metrics across all turns."""
        latencies = []
        filler_counts = []
        durations = []
        word_counts = []
        filler_rates = []
        shortest_answer = None
        shortest_duration = float("inf")

        for turn in history:
            vm = turn.voice_metrics
            if not vm:
                continue

            lat = vm.get("response_latency_s")
            if lat is not None:
                latencies.append(lat)

            fc = vm.get("filler_count", 0)
            filler_counts.append(fc)

            dur = vm.get("answer_duration_s", 0)
            if dur > 0:
                durations.append(dur)
                if dur < shortest_duration:
                    shortest_duration = dur
                    shortest_answer = {
                        "turn_number": turn.turn_number,
                        "question_preview": turn.question[:80],
                        "duration_s": dur,
                    }

            wc = vm.get("word_count", 0)
            word_counts.append(wc)

            fr = vm.get("filler_rate_per_min", 0)
            filler_rates.append(fr)

        if not durations:
            return {"has_voice_data": False}

        return {
            "has_voice_data": True,
            "avg_response_latency_s": (
                round(sum(latencies) / len(latencies), 2) if latencies else None
            ),
            "avg_filler_rate_per_min": (
                round(sum(filler_rates) / len(filler_rates), 2) if filler_rates else 0
            ),
            "total_filler_count": sum(filler_counts),
            "avg_answer_duration_s": round(sum(durations) / len(durations), 2),
            "avg_word_count": round(sum(word_counts) / len(word_counts), 1),
            "shortest_answer": shortest_answer,
        }

    def _generate_scorecard(
        self,
        per_question: list[dict],
        consistency: dict,
        hint_analysis: dict,
        voice_summary: dict,
        state: InterviewState,
    ) -> dict:
        """Use LLM to generate overall scorecard and action plan."""
        eval_data = {
            "company": state.company,
            "role": state.role,
            "per_question_summary": [
                {
                    "persona": q["persona"],
                    "quality": q["quality"],
                    "confidence": q["confidence_score"],
                    "specificity": q["specificity_score"],
                    "star_score": q["star"]["score"],
                    "flags": q["flags"],
                    "hint_used": q["hint_used"],
                }
                for q in per_question
            ],
            "consistency": {
                "consistent": consistency.get("consistent", True),
                "contradiction_count": len(consistency.get("contradictions", [])),
            },
            "hint_analysis": hint_analysis,
            "voice_summary": voice_summary,
            "flags": state.flags,
        }

        system = (
            "You are an expert interview performance evaluator. "
            "Analyze the interview data and produce a scorecard. "
            "Return ONLY valid JSON."
        )
        prompt = f"""Analyze this interview performance data and generate a scorecard:

{json.dumps(eval_data, ensure_ascii=False)}

Return JSON with:
- "overall_score": 1-100 overall interview performance
- "persona_scores": {{"HM": score, "Tech": score, "HR": score}} (1-100 each, only include personas that asked questions)
- "strengths": list of 3-5 key strengths demonstrated
- "weaknesses": list of 3-5 areas needing improvement
- "action_plan": list of 5-7 specific, actionable steps to improve for the next interview

Be fair but honest. Consider:
- Answer quality distribution (strong/adequate/weak)
- STAR framework usage
- Consistency across answers
- Hint dependency
- Voice metrics (if available)
- Specific flags raised during interview"""

        text, _ = self.llm.converse(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=3000,
            temperature=0.3,
        )
        return _parse_json_safe(text)


def _safe_json(text: str) -> dict:
    """Parse JSON from tool output, returning empty dict on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"raw": text}


def _parse_json_safe(text: str) -> dict:
    """Try to extract JSON from LLM response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for start_delim, end_delim in [("```json", "```"), ("```", "```")]:
        try:
            start = text.index(start_delim) + len(start_delim)
            end = text.index(end_delim, start)
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            continue
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"raw_response": text}


def _truncate_dict(d: dict, max_chars: int) -> dict:
    """Truncate a dict's JSON representation for LLM context limits."""
    s = json.dumps(d, ensure_ascii=False)
    if len(s) <= max_chars:
        return d
    try:
        return json.loads(s[:max_chars - 3] + "}")
    except json.JSONDecodeError:
        return {}
