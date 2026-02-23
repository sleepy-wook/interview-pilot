"""Interview state management."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TurnRecord:
    """Record of a single interview turn."""
    turn_number: int
    persona: str
    question: str
    answer: str = ""
    hint_bullets: dict = field(default_factory=dict)
    hint_used: bool = False
    answer_analysis: dict = field(default_factory=dict)
    voice_metrics: dict = field(default_factory=dict)


@dataclass
class InterviewState:
    """Mutable state for a live interview session."""
    session_id: str
    company: str
    role: str
    mode: str = "practice"  # "practice" | "real"
    model: str = "haiku"  # "haiku" | "sonnet"
    question_count: int = 10  # configurable, 5-20 range

    # Ice breaker state
    ice_breaker_done: bool = False

    # Phase 1 output
    interview_plan: list[dict] = field(default_factory=list)

    # Phase 2 live state
    current_index: int = 0
    answer_history: list[TurnRecord] = field(default_factory=list)
    persona_memories: dict = field(default_factory=lambda: {"HM": [], "Tech": [], "HR": []})
    flags: list[str] = field(default_factory=list)
    coverage: dict = field(default_factory=lambda: {"covered": [], "remaining": []})
    dynamic_questions: list[dict] = field(default_factory=list)

    # Hint tracking
    hint_log: list[dict] = field(default_factory=list)

    # Research Brief (set after Phase 0)
    research_brief: dict = field(default_factory=dict)
