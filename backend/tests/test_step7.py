"""Step 7 Tests: Evaluation Agent + Report.

Tests the full evaluation pipeline:
- Per-question STAR evaluation
- Consistency check
- Model answer generation for weak answers
- Hint usage analysis
- Voice metrics aggregation
- Overall scorecard + action plan via LLM
"""

import sys
import os

# Fix Windows cp949 encoding for Unicode output
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

# Import tools so they register
import tools.web_search  # noqa: F401
import tools.web_scrape  # noqa: F401
import tools.llm_tools  # noqa: F401
import tools.document_reader  # noqa: F401

from tools.registry import global_registry
from agents.evaluation_agent import EvaluationAgent
from core.state import InterviewState, TurnRecord

# Build a realistic completed interview state for testing
SAMPLE_BRIEF = {
    "company_profile": {
        "name": "Databricks",
        "description": "Data and AI company with unified Data Intelligence Platform.",
        "products": ["Lakehouse", "Delta Lake", "Spark", "MLflow", "Mosaic AI"],
    },
    "jd_structured": {
        "requirements": [
            "Experience with big data technologies (Spark, Hadoop)",
            "Cloud platform experience (AWS, Azure, GCP)",
            "Customer-facing technical experience",
            "Python and SQL proficiency",
        ],
        "keywords": ["Spark", "Delta Lake", "Lakehouse", "SQL", "Python", "AWS"],
    },
    "candidate_profile": {
        "name": "John Doe",
        "current_role": "Senior Data Engineer at TechCorp",
        "experience_years": 5,
        "skills": ["Python", "SQL", "Spark", "Kafka", "AWS", "Docker"],
    },
    "gap_analysis": {
        "gaps": [
            {"requirement": "Customer-facing experience", "severity": "moderate"},
        ],
    },
    "keywords": ["Spark", "Delta Lake", "Lakehouse", "MLflow"],
}

SAMPLE_PLAN = [
    {"question": "Tell me about yourself", "persona": "HM", "topic": "introduction", "depth": "surface", "priority": "high"},
    {"question": "Explain Spark internals", "persona": "Tech", "topic": "spark", "depth": "deep", "priority": "high"},
    {"question": "Describe a conflict resolution", "persona": "HR", "topic": "conflict", "depth": "moderate", "priority": "medium"},
    {"question": "How would you run a POC?", "persona": "HM", "topic": "poc-process", "depth": "moderate", "priority": "high"},
    {"question": "What is Delta Lake?", "persona": "Tech", "topic": "delta-lake", "depth": "moderate", "priority": "medium"},
]

# Pre-built answer history simulating a completed interview
SAMPLE_TURNS = [
    TurnRecord(
        turn_number=1,
        persona="HM",
        question="Tell me about yourself and why you're interested in Databricks.",
        answer=(
            "I've been a data engineer for 5 years at TechCorp, building real-time pipelines "
            "with Spark and Kafka. In my last project, we migrated 50TB of data to a lakehouse "
            "architecture, reducing query times by 60%. I led workshops for 50+ enterprise clients. "
            "I'm excited about Databricks because your platform is the gold standard for what I've been building."
        ),
        answer_analysis={
            "quality": "strong",
            "confidence_score": 85,
            "specificity_score": 80,
            "star_score": 70,
            "flags": [],
        },
        hint_used=False,
        voice_metrics={
            "response_latency_s": 2.1,
            "answer_duration_s": 45.3,
            "filler_count": 2,
            "filler_rate_per_min": 2.6,
            "word_count": 78,
        },
    ),
    TurnRecord(
        turn_number=2,
        persona="Tech",
        question="Can you explain how Spark handles distributed data processing and fault tolerance?",
        answer=(
            "Um, Spark processes data in memory which makes it fast. "
            "I think it uses RDDs... or maybe DataFrames. I've used it at my job "
            "but I'm not really sure about the internal architecture details."
        ),
        answer_analysis={
            "quality": "weak",
            "confidence_score": 30,
            "specificity_score": 20,
            "star_score": 10,
            "flags": ["vague", "uncertain"],
        },
        hint_used=True,
        voice_metrics={
            "response_latency_s": 4.5,
            "answer_duration_s": 15.2,
            "filler_count": 5,
            "filler_rate_per_min": 19.7,
            "word_count": 35,
        },
    ),
    TurnRecord(
        turn_number=3,
        persona="HR",
        question="Tell me about a time you resolved a conflict with a team member.",
        answer=(
            "At TechCorp, I had a disagreement with a senior developer about data pipeline "
            "architecture. He wanted to use batch processing but I believed real-time was better "
            "for our use case. I set up a POC comparing both approaches with actual production data. "
            "After seeing the results, we agreed on a hybrid approach that satisfied both requirements. "
            "The project delivered 30% faster insights to the business."
        ),
        answer_analysis={
            "quality": "strong",
            "confidence_score": 82,
            "specificity_score": 78,
            "star_score": 85,
            "flags": [],
        },
        hint_used=False,
        voice_metrics={
            "response_latency_s": 3.0,
            "answer_duration_s": 38.5,
            "filler_count": 1,
            "filler_rate_per_min": 1.6,
            "word_count": 65,
        },
    ),
    TurnRecord(
        turn_number=4,
        persona="HM",
        question="How would you approach running a POC for a major enterprise customer?",
        answer=(
            "I would start by understanding the customer's specific pain points and requirements. "
            "Then I'd design a POC that addresses those directly. I think a POC is important. "
            "We'd work with their data if possible."
        ),
        answer_analysis={
            "quality": "adequate",
            "confidence_score": 55,
            "specificity_score": 40,
            "star_score": 25,
            "flags": ["vague"],
        },
        hint_used=True,
        voice_metrics={
            "response_latency_s": 3.8,
            "answer_duration_s": 20.1,
            "filler_count": 3,
            "filler_rate_per_min": 9.0,
            "word_count": 42,
        },
    ),
    TurnRecord(
        turn_number=5,
        persona="Tech",
        question="What are the key benefits of Delta Lake over traditional data lakes?",
        answer=(
            "Delta Lake provides ACID transactions on top of data lakes, which is huge for "
            "reliability. It also has schema enforcement and time travel capabilities. "
            "At TechCorp, we used Parquet files but constantly had issues with data corruption "
            "during concurrent writes. Delta Lake solves that with its transaction log."
        ),
        answer_analysis={
            "quality": "adequate",
            "confidence_score": 70,
            "specificity_score": 65,
            "star_score": 40,
            "flags": [],
        },
        hint_used=False,
        voice_metrics={
            "response_latency_s": 2.5,
            "answer_duration_s": 30.0,
            "filler_count": 1,
            "filler_rate_per_min": 2.0,
            "word_count": 55,
        },
    ),
]


def _build_test_state() -> InterviewState:
    """Build a completed interview state for testing."""
    state = InterviewState(
        session_id="eval-test-001",
        company="Databricks",
        role="Solutions Engineer",
        research_brief=SAMPLE_BRIEF,
        interview_plan=SAMPLE_PLAN,
        current_index=5,  # All 5 planned questions asked
        answer_history=list(SAMPLE_TURNS),
        flags=["Tech_spark: vague", "Tech_spark: uncertain", "HM_poc-process: vague"],
        coverage={
            "covered": ["introduction", "spark", "conflict", "poc-process", "delta-lake"],
            "remaining": [],
        },
    )
    return state


def test_per_question_evaluation():
    """Test: Per-question STAR evaluation runs on all answers."""
    print("=== Test 1: Per-question STAR Evaluation ===")

    state = _build_test_state()
    evaluator = EvaluationAgent(registry=global_registry)

    per_question = evaluator._evaluate_per_question(state.answer_history, state)

    print(f"  Evaluated {len(per_question)} questions")
    for pq in per_question:
        star = pq["star"]
        star_parts = sum([star["situation"], star["task"], star["action"], star["result"]])
        print(
            f"  Turn {pq['turn_number']} [{pq['persona']}]: "
            f"quality={pq['quality']}, STAR={star['score']}/100 ({star_parts}/4 parts)"
        )

    assert len(per_question) == 5, f"Expected 5, got {len(per_question)}"
    # Each entry should have STAR data
    for pq in per_question:
        assert "star" in pq, f"Turn {pq['turn_number']} missing STAR data"
        assert "score" in pq["star"], f"Turn {pq['turn_number']} STAR missing score"

    print("[PASS] Per-question evaluation complete")
    return per_question


def test_model_answer_generation():
    """Test: Model answers generated for weak/adequate answers."""
    print("\n=== Test 2: Model Answer Generation ===")

    state = _build_test_state()
    evaluator = EvaluationAgent(registry=global_registry)

    model_answers = evaluator._generate_model_answers(state.answer_history, state)

    print(f"  Generated {len(model_answers)} model answers")
    for ma in model_answers:
        preview = ma.get("improved_answer", "")[:80]
        print(
            f"  Turn {ma['turn_number']}: {ma['original_quality']} -> "
            f"score {ma.get('score_before', '?')}->{ma.get('score_after', '?')}"
        )
        if preview:
            print(f"    Preview: {preview}...")

    # Should generate for weak (turn 2) and adequate (turns 4, 5)
    assert len(model_answers) >= 2, f"Expected at least 2 model answers, got {len(model_answers)}"

    # Verify weak answer (turn 2) gets a model answer
    weak_turns = [ma for ma in model_answers if ma["original_quality"] == "weak"]
    assert len(weak_turns) >= 1, "No model answer generated for weak answer"

    print("[PASS] Model answers generated for weak/adequate answers")


def test_hint_and_voice_analysis():
    """Test: Hint usage analysis and voice metrics aggregation."""
    print("\n=== Test 3: Hint & Voice Analysis ===")

    state = _build_test_state()
    evaluator = EvaluationAgent(registry=global_registry)

    # Hint analysis
    hint_analysis = evaluator._analyze_hints(state.answer_history, state)
    print(f"  Hint usage: {hint_analysis['hints_used']}/{hint_analysis['total_questions']}")
    print(f"  Breakdown: {hint_analysis['breakdown']}")
    print(f"  Focus topics: {hint_analysis['focus_topics']}")

    assert hint_analysis["total_questions"] == 5
    assert hint_analysis["hints_used"] == 2  # Turns 2 and 4
    assert hint_analysis["hints_not_used"] == 3

    # Voice analysis
    voice_summary = evaluator._summarize_voice_metrics(state.answer_history)
    print(f"\n  Voice data available: {voice_summary['has_voice_data']}")
    print(f"  Avg response latency: {voice_summary.get('avg_response_latency_s')}s")
    print(f"  Avg filler rate: {voice_summary.get('avg_filler_rate_per_min')}/min")
    print(f"  Total fillers: {voice_summary.get('total_filler_count')}")
    if voice_summary.get("shortest_answer"):
        sa = voice_summary["shortest_answer"]
        print(f"  Shortest answer: Turn {sa['turn_number']} ({sa['duration_s']}s)")

    assert voice_summary["has_voice_data"] is True
    assert voice_summary["avg_response_latency_s"] is not None
    assert voice_summary["total_filler_count"] == 12  # 2+5+1+3+1

    print("[PASS] Hint and voice analysis correct")


def test_full_evaluation_pipeline():
    """Test: Full evaluation pipeline end-to-end."""
    print("\n=== Test 4: Full Evaluation Pipeline ===")

    state = _build_test_state()
    evaluator = EvaluationAgent(registry=global_registry)

    report = evaluator.evaluate(state)

    # Check all required fields
    required_keys = [
        "overall_score", "persona_scores", "strengths", "weaknesses",
        "per_question", "consistency", "hint_analysis", "voice_summary",
        "model_answers", "action_plan",
    ]
    for key in required_keys:
        assert key in report, f"Missing key: {key}"

    print(f"  Overall score: {report['overall_score']}/100")
    print(f"  Persona scores: {report['persona_scores']}")
    print(f"  Strengths: {len(report['strengths'])} items")
    print(f"  Weaknesses: {len(report['weaknesses'])} items")
    print(f"  Model answers: {len(report['model_answers'])} generated")
    print(f"  Action plan: {len(report['action_plan'])} items")
    print(f"  Per-question: {len(report['per_question'])} evaluations")
    print(f"  Consistency: consistent={report['consistency'].get('consistent')}")

    # Validate scores
    overall = report["overall_score"]
    assert isinstance(overall, (int, float)), f"Overall score not numeric: {overall}"
    assert 1 <= overall <= 100, f"Overall score out of range: {overall}"

    # Validate persona scores exist
    persona_scores = report["persona_scores"]
    assert isinstance(persona_scores, dict), "Persona scores not a dict"
    # At least HM and Tech should have scores (they both asked questions)
    assert len(persona_scores) >= 2, f"Expected at least 2 persona scores, got {len(persona_scores)}"

    # Validate action plan
    action_plan = report["action_plan"]
    assert len(action_plan) >= 3, f"Action plan too short: {len(action_plan)} items"

    # Print action plan
    print("\n  Action Plan:")
    for i, item in enumerate(action_plan[:5], 1):
        text = item if isinstance(item, str) else str(item)
        print(f"    {i}. {text[:100]}")

    print("\n[PASS] Full evaluation pipeline complete")


if __name__ == "__main__":
    passed = 0
    failed = 0

    # Test 1: Per-question STAR evaluation
    try:
        test_per_question_evaluation()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_per_question_evaluation: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # Test 2: Model answer generation
    try:
        test_model_answer_generation()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_model_answer_generation: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # Test 3: Hint and voice analysis
    try:
        test_hint_and_voice_analysis()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_hint_and_voice_analysis: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # Test 4: Full evaluation pipeline
    try:
        test_full_evaluation_pipeline()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_full_evaluation_pipeline: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All Step 7 tests PASSED!")
