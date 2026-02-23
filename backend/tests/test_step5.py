"""Step 5 Tests: Persona Agents + Interview Loop (TEXT MODE).

Runs a full text-based interview:
- Master generates plan
- 5 questions with hints
- Pre-scripted answers (mix of good and weak)
- Verify routing, consistency check, hints
"""

import sys
import os
import json

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
from agents.persona_agents import HMPersona, TechPersona, HRPersona
from agents.master_agent import MasterAgent
from core.state import InterviewState

# Sample Research Brief (realistic, from Step 4 output)
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
            "Understanding of data architecture patterns",
        ],
        "responsibilities": [
            "Deliver technical solutions to enterprise customers",
            "Conduct POCs and technical workshops",
            "Partner with sales team on deals",
        ],
        "keywords": ["Spark", "Delta Lake", "Lakehouse", "SQL", "Python", "AWS"],
    },
    "candidate_profile": {
        "name": "John Doe",
        "current_role": "Senior Data Engineer at TechCorp",
        "experience_years": 5,
        "skills": ["Python", "SQL", "Spark", "Kafka", "AWS", "Docker"],
        "education": "B.S. Computer Science, UC Berkeley",
    },
    "gap_analysis": {
        "matches": [
            {"requirement": "Python and SQL", "strength": "strong"},
            {"requirement": "Cloud platform (AWS)", "strength": "strong"},
            {"requirement": "Big data (Spark)", "strength": "moderate"},
        ],
        "gaps": [
            {"requirement": "Customer-facing experience", "severity": "moderate"},
            {"requirement": "Databricks platform knowledge", "severity": "moderate"},
        ],
    },
    "predicted_weak_points": [
        "Limited customer-facing experience",
        "No direct Databricks platform experience",
        "May struggle with SE-specific scenario questions",
    ],
    "keywords": ["Spark", "Delta Lake", "Lakehouse", "MLflow", "Unity Catalog"],
}

# Pre-scripted answers for testing (mix of quality levels)
SCRIPTED_ANSWERS = [
    # Answer 1: Good answer (HM-style question)
    (
        "I've been working as a data engineer for 5 years at TechCorp, where I built "
        "real-time data pipelines using Spark and Kafka. I'm excited about Databricks "
        "because the Lakehouse architecture aligns with what I've been building -- "
        "combining the best of data warehouses and data lakes. I also led customer-facing "
        "workshops for 50+ enterprise clients, which gave me a taste of the SE role."
    ),
    # Answer 2: Weak answer (Tech-style question)
    (
        "Um, I think Spark is fast because it processes data in memory. "
        "I've used it at my job but I'm not sure about the internals."
    ),
    # Answer 3: Good answer (HR-style question)
    (
        "In five years, I see myself as a senior Solutions Engineer or potentially "
        "leading a team of SEs. I want to deepen my expertise in data architecture "
        "and become a trusted advisor for enterprise customers. I'm also interested "
        "in contributing to Databricks' open-source projects like Delta Lake."
    ),
    # Answer 4: Evasive answer (to trigger follow-up)
    (
        "I prefer not to discuss specific salary numbers at this stage. "
        "I'm flexible and open to negotiation."
    ),
    # Answer 5: Contradictory with answer 1 (claims no customer experience)
    (
        "To be honest, I haven't had much customer-facing experience. "
        "My work has been mostly backend data engineering with little client interaction. "
        "I'm hoping to develop those skills in this role."
    ),
]


def test_plan_generation():
    """Test: Master generates interview plan from Research Brief."""
    print("=== Test 1: Interview Plan Generation ===")

    state = InterviewState(
        session_id="test-001",
        company="Databricks",
        role="Solutions Engineer",
        research_brief=SAMPLE_BRIEF,
    )
    personas = {
        "HM": HMPersona(registry=global_registry),
        "Tech": TechPersona(registry=global_registry),
        "HR": HRPersona(registry=global_registry),
    }
    master = MasterAgent(
        registry=global_registry,
        state=state,
        personas=personas,
    )

    plan = master.generate_plan()

    print(f"  Plan length: {len(plan)} questions")
    if plan:
        persona_counts = {}
        for q in plan:
            p = q.get("persona", "?")
            persona_counts[p] = persona_counts.get(p, 0) + 1
        print(f"  Persona distribution: {persona_counts}")
        first_q = plan[0].get("question", "").encode("ascii", "replace").decode()
        print(f"  First question: [{plan[0].get('persona')}] {first_q[:70]}")

    assert len(plan) >= 5, f"Plan too short: {len(plan)} questions"
    print("[PASS] Interview plan generated")

    return master, state, personas


def test_interview_loop(master, state, personas):
    """Test: Run 5-turn text interview with routing and analysis."""
    print("\n=== Test 2: Interview Loop (5 turns) ===")

    hints_generated = 0
    analyses_done = 0
    consistency_checked = False

    for i, scripted_answer in enumerate(SCRIPTED_ANSWERS):
        turn_num = i + 1
        print(f"\n  --- Turn {turn_num} ---")

        # Get next question
        q_data = master.get_next_question()
        if q_data is None:
            print(f"  Interview ended at turn {turn_num}")
            break

        question = q_data["question"]
        persona = q_data["persona"]
        hints = q_data.get("hints", {})

        print(f"  [{persona}] Q: {question[:80]}...")

        # Check hints
        if hints and (hints.get("bullets") or hints.get("personal_hooks")):
            hints_generated += 1
            bullet_count = len(hints.get("bullets", []))
            print(f"  Hints: {bullet_count} bullets")

        # Submit answer
        print(f"  A: {scripted_answer[:60]}...")
        result = master.process_answer(question, scripted_answer, persona)

        analysis = result.get("analysis", {})
        quality = analysis.get("quality", "?")
        routing = result.get("routing", {})
        next_action = routing.get("action", "?")
        next_persona = routing.get("next_persona", "?")

        print(f"  Quality: {quality} | Next: {next_action} -> {next_persona}")
        analyses_done += 1

        # Check consistency
        if result.get("consistency") is not None:
            consistency_checked = True
            is_consistent = result["consistency"].get("consistent", True)
            contradictions = len(result["consistency"].get("contradictions", []))
            print(f"  Consistency: {'OK' if is_consistent else f'{contradictions} contradictions'}")

    # Verify results
    print(f"\n  Summary:")
    print(f"  - Hints generated: {hints_generated}/5")
    print(f"  - Analyses done: {analyses_done}/5")
    print(f"  - Consistency checked: {consistency_checked}")
    print(f"  - Flags: {state.flags[:3]}")

    assert analyses_done >= 4, f"Only {analyses_done} analyses completed"
    assert hints_generated >= 3, f"Only {hints_generated} hints generated"
    print("[PASS] Interview loop ran successfully")

    return state


def test_persona_memory(personas):
    """Test: Persona independent memory and cross-observation."""
    print("\n=== Test 3: Persona Memory ===")

    has_memory = False
    has_observations = False

    for p_type, persona in personas.items():
        qa_count = len(persona.qa_memory)
        obs_count = len(persona.observations)
        if qa_count > 0:
            has_memory = True
        if obs_count > 0:
            has_observations = True
        print(f"  {p_type}: {qa_count} Q&A, {obs_count} observations")

    assert has_memory, "No persona recorded any Q&A"
    assert has_observations, "No cross-persona observations recorded"
    print("[PASS] Persona memory working")


def test_state_tracking(state):
    """Test: Interview state properly tracked."""
    print("\n=== Test 4: State Tracking ===")

    print(f"  Answer history: {len(state.answer_history)} turns")
    print(f"  Current index: {state.current_index}")
    print(f"  Topics covered: {len(state.coverage.get('covered', []))}")
    print(f"  Flags: {len(state.flags)}")

    assert len(state.answer_history) >= 4, "Not enough turns recorded"
    assert state.current_index >= 4, "Current index not advanced"
    print("[PASS] State tracking correct")


if __name__ == "__main__":
    passed = 0
    failed = 0

    # Test 1: Plan generation
    master = state = personas = None
    try:
        master, state, personas = test_plan_generation()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_plan_generation: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # Test 2: Interview loop (depends on test 1)
    if master:
        try:
            state = test_interview_loop(master, state, personas)
            passed += 1
        except Exception as e:
            print(f"[FAIL] test_interview_loop: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

        # Test 3: Persona memory
        try:
            test_persona_memory(personas)
            passed += 1
        except Exception as e:
            print(f"[FAIL] test_persona_memory: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

        # Test 4: State tracking
        try:
            test_state_tracking(state)
            passed += 1
        except Exception as e:
            print(f"[FAIL] test_state_tracking: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    else:
        print("\n[SKIP] Tests 2-4 skipped (plan generation failed)")
        failed += 3

    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All Step 5 tests PASSED!")
