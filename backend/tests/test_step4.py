"""Step 4 Tests: Research Agent + Resume Agent + merge (E2E Phase 0)."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

# Import tools so they register via @register_tool
import tools.web_search  # noqa: F401
import tools.web_scrape  # noqa: F401
import tools.llm_tools  # noqa: F401
import tools.document_reader  # noqa: F401

from tools.registry import global_registry
from agents.research_agent import ResearchAgent
from agents.resume_agent import ResumeAgent
from agents import merge_research_brief


def _create_sample_resume_pdf(path: str) -> None:
    """Create a minimal sample resume PDF for testing."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "John Doe", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "johndoe@email.com | (555) 123-4567 | San Francisco, CA", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5,
        "Data engineer with 5 years of experience in cloud platforms (AWS, GCP), "
        "Python, SQL, and big data technologies. Passionate about helping customers "
        "adopt data-driven solutions. AWS Solutions Architect Associate certified."
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Work Experience", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Senior Data Engineer - TechCorp Inc. (2022 - Present)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5,
        "- Built real-time data pipelines using Apache Spark and Kafka\n"
        "- Led migration of on-premise data warehouse to AWS (Redshift, S3, Glue)\n"
        "- Conducted technical workshops for 50+ enterprise customers\n"
        "- Reduced data processing costs by 40% through optimization"
    )
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Data Engineer - DataStart LLC (2020 - 2022)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5,
        "- Developed ETL pipelines with Python, Airflow, and PostgreSQL\n"
        "- Built ML feature store for recommendation engine\n"
        "- Collaborated with cross-functional teams on data platform strategy"
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Skills", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5,
        "Python, SQL, Apache Spark, Kafka, AWS (S3, Redshift, Glue, Lambda), "
        "GCP (BigQuery), Docker, Kubernetes, Terraform, Git, Airflow, dbt, "
        "PostgreSQL, Machine Learning basics, REST APIs"
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Education", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "B.S. Computer Science - UC Berkeley (2016 - 2020)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Certifications", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "- AWS Solutions Architect Associate", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "- Databricks Certified Data Engineer Associate", new_x="LMARGIN", new_y="NEXT")

    pdf.output(path)


def test_research_agent():
    """Test Research Agent with real web search (Databricks SE)."""
    print("=== Test 1: Research Agent ===")
    print("  (This may take 30-60 seconds due to web search + LLM calls)")

    agent = ResearchAgent(registry=global_registry)
    result = agent.research(company="Databricks", role="Solutions Engineer")

    print(f"  Keys: {list(result.keys())}")

    # Check for essential keys
    has_company = "company_profile" in result
    has_jd = "jd_structured" in result
    has_keywords = "keywords" in result
    has_raw = "raw_response" in result

    if has_raw:
        print(f"  [WARN] Agent returned raw text (JSON parse failed)")
        print(f"  Raw (first 200 chars): {result['raw_response'][:200]}")
        # Still pass if we got something back
        assert len(result["raw_response"]) > 50
        print("[PASS] Research Agent returned results (raw text)")
    else:
        print(f"  Company profile: {'yes' if has_company else 'no'}")
        print(f"  JD structured: {'yes' if has_jd else 'no'}")
        print(f"  Keywords: {'yes' if has_keywords else 'no'}")
        assert has_company or has_jd or has_keywords, "No useful keys in research output"
        print("[PASS] Research Agent returned structured results")

    return result


def test_resume_agent(jd_structured: dict):
    """Test Resume Agent with sample PDF."""
    print("\n=== Test 2: Resume Agent ===")
    print("  (This may take 30-60 seconds due to Vision + LLM calls)")

    # Create sample PDF
    sample_pdf = os.path.join(os.path.dirname(__file__), "sample_resume.pdf")
    _create_sample_resume_pdf(sample_pdf)
    print(f"  Created sample PDF: {sample_pdf}")

    agent = ResumeAgent(registry=global_registry)
    result = agent.analyze(
        resume_path=sample_pdf,
        jd_structured=jd_structured,
    )

    print(f"  Keys: {list(result.keys())}")

    has_profile = "candidate_profile" in result
    has_gap = "gap_analysis" in result
    has_raw = "raw_response" in result

    if has_raw:
        print(f"  [WARN] Agent returned raw text (JSON parse failed)")
        print(f"  Raw (first 200 chars): {result['raw_response'][:200]}")
        assert len(result["raw_response"]) > 50
        print("[PASS] Resume Agent returned results (raw text)")
    else:
        print(f"  Candidate profile: {'yes' if has_profile else 'no'}")
        print(f"  Gap analysis: {'yes' if has_gap else 'no'}")
        assert has_profile or has_gap, "No useful keys in resume output"
        print("[PASS] Resume Agent returned structured results")

    # Cleanup
    if os.path.exists(sample_pdf):
        os.remove(sample_pdf)

    return result


def test_merge(research_output: dict, resume_output: dict):
    """Test merge logic."""
    print("\n=== Test 3: Merge Research Brief ===")

    brief = merge_research_brief(research_output, resume_output)

    print(f"  Brief keys: {list(brief.keys())}")
    expected_keys = [
        "company_profile", "jd_structured", "candidate_profile",
        "gap_analysis", "interview_tips", "predicted_weak_points",
        "talking_points", "keywords", "competitive_landscape",
    ]
    for key in expected_keys:
        assert key in brief, f"Missing key: {key}"

    print("[PASS] Research Brief has all expected keys")

    # Pretty-print the brief for user review
    print("\n" + "=" * 60)
    print("RESEARCH BRIEF (for quality review)")
    print("=" * 60)
    print(json.dumps(brief, indent=2, ensure_ascii=False)[:3000])
    if len(json.dumps(brief, ensure_ascii=False)) > 3000:
        print("\n... [truncated for display]")
    print("=" * 60)

    return brief


if __name__ == "__main__":
    tests_passed = 0
    tests_failed = 0

    # Test 1: Research Agent
    research_output = {}
    try:
        research_output = test_research_agent()
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] test_research_agent: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1

    # Test 2: Resume Agent (uses JD from research if available)
    jd_for_resume = research_output.get("jd_structured", {
        "requirements": ["5+ years data engineering", "Apache Spark", "Cloud platforms"],
        "responsibilities": ["Customer-facing technical solutions", "Data architecture"],
        "keywords": ["Spark", "Databricks", "SQL", "Python", "AWS"],
    })

    resume_output = {}
    try:
        resume_output = test_resume_agent(jd_for_resume)
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] test_resume_agent: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1

    # Test 3: Merge
    try:
        test_merge(research_output, resume_output)
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] test_merge: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1

    print(f"\n{'=' * 40}")
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    if tests_failed == 0:
        print("All Step 4 tests PASSED!")
