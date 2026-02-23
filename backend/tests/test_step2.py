"""Step 2 Tests: LLM-powered tools + document_reader."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

# Import tools to trigger @register_tool decorators
import tools.llm_tools  # noqa: F401
import tools.document_reader  # noqa: F401
from tools.registry import global_registry


def test_tool_registration():
    """Verify all tools are registered."""
    print("=== Test: Tool Registration ===")
    expected = [
        "jd_parser", "gap_analyzer", "question_generator", "hint_generator",
        "answer_analyzer", "persona_router", "star_detector",
        "consistency_checker", "answer_improver", "document_reader",
    ]
    registered = global_registry.tool_names
    print(f"  Registered tools: {registered}")

    for name in expected:
        assert name in registered, f"Tool '{name}' not registered!"
    print(f"  All {len(expected)} tools registered")
    print("[PASS] Tool Registration")


def test_answer_analyzer_good_vs_bad():
    """Test answer_analyzer distinguishes good and bad answers."""
    print("\n=== Test: answer_analyzer (good vs bad) ===")

    good_answer = (
        "At my previous company, we faced a critical data pipeline failure during a product launch. "
        "I was tasked with identifying the root cause and restoring service within 4 hours. "
        "I systematically analyzed the logs, identified a schema mismatch in our Delta Lake tables, "
        "and implemented a hotfix using Spark Structured Streaming. "
        "As a result, we restored service in 2.5 hours and I later built automated schema validation "
        "that prevented similar issues, reducing pipeline failures by 80%."
    )
    bad_answer = "Um, yeah, I think I did something like that once. It was fine, I guess."

    good_result = json.loads(global_registry.execute("answer_analyzer", {
        "question": "Tell me about a time you solved a critical technical problem.",
        "answer": good_answer,
        "persona": "Tech",
    }))
    print(f"  Good answer quality: {good_result.get('quality')}")
    print(f"  Good answer confidence: {good_result.get('confidence_score')}")

    bad_result = json.loads(global_registry.execute("answer_analyzer", {
        "question": "Tell me about a time you solved a critical technical problem.",
        "answer": bad_answer,
        "persona": "Tech",
    }))
    print(f"  Bad answer quality: {bad_result.get('quality')}")
    print(f"  Bad answer confidence: {bad_result.get('confidence_score')}")

    assert good_result.get("quality") in ("strong", "adequate")
    assert bad_result.get("quality") in ("weak", "evasive")
    print("[PASS] answer_analyzer correctly distinguished good vs bad")


def test_hint_generator():
    """Test hint_generator produces personalized hints."""
    print("\n=== Test: hint_generator ===")

    result = json.loads(global_registry.execute("hint_generator", {
        "question": "Explain how Delta Lake implements ACID transactions.",
        "persona": "Tech",
        "resume_context": {
            "projects": [{"name": "Orbital Junkyard", "tech": "Delta Lake, Spark, CesiumJS"}],
            "skills": ["Python", "Spark", "Delta Lake", "AWS"],
        },
        "research_brief_context": {
            "company": "Databricks",
            "jd_keywords": ["Delta Lake", "ACID", "Spark"],
        },
    }))

    print(f"  Bullets count: {len(result.get('bullets', []))}")
    print(f"  Personal hooks count: {len(result.get('personal_hooks', []))}")

    assert "bullets" in result
    assert len(result["bullets"]) >= 2
    assert "personal_hooks" in result
    print("[PASS] hint_generator produced personalized hints")


def test_star_detector():
    """Test star_detector identifies STAR components."""
    print("\n=== Test: star_detector ===")

    star_answer = (
        "When I was at Samsung, our data pipeline was processing 50TB daily but failing frequently. "
        "I was responsible for redesigning the pipeline architecture. "
        "I migrated the system from batch processing to Spark Structured Streaming with Delta Lake, "
        "implemented proper error handling and monitoring. "
        "As a result, pipeline reliability improved from 85% to 99.5% and processing time was cut by 60%."
    )

    result = json.loads(global_registry.execute("star_detector", {"answer": star_answer}))

    print(f"  Situation present: {result.get('situation', {}).get('present')}")
    print(f"  Task present: {result.get('task', {}).get('present')}")
    print(f"  Action present: {result.get('action', {}).get('present')}")
    print(f"  Result present: {result.get('result', {}).get('present')}")
    print(f"  STAR score: {result.get('score')}")

    assert result.get("score", 0) >= 50
    print("[PASS] star_detector identified STAR components")


def test_consistency_checker():
    """Test consistency_checker detects contradictions."""
    print("\n=== Test: consistency_checker ===")

    result = json.loads(global_registry.execute("consistency_checker", {
        "answers": [
            {"question": "What is your role?", "answer": "I lead a team of 5 engineers on AI projects.", "persona": "HM"},
            {"question": "What data scale do you work with?", "answer": "Mostly personal project scale, nothing large.", "persona": "Tech"},
        ]
    }))

    print(f"  Consistent: {result.get('consistent')}")
    print(f"  Contradictions: {result.get('contradictions', [])}")

    assert result.get("consistent") is False or len(result.get("contradictions", [])) > 0 or len(result.get("concerns", [])) > 0
    print("[PASS] consistency_checker detected issues")


if __name__ == "__main__":
    tests = [
        test_tool_registration,
        test_answer_analyzer_good_vs_bad,
        test_hint_generator,
        test_star_detector,
        test_consistency_checker,
    ]
    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All Step 2 tests PASSED!")
