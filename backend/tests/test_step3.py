"""Step 3 Tests: web_search and web_scrape tools."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

import tools.web_search  # noqa: F401
import tools.web_scrape  # noqa: F401
from tools.registry import global_registry


def test_web_search():
    """Test web_search returns results for a query."""
    print("=== Test: web_search ===")

    result = json.loads(global_registry.execute("web_search", {
        "query": "Databricks Solutions Engineer job posting",
        "num_results": 3,
    }))

    print(f"  Query: {result.get('query')}")
    print(f"  Results count: {len(result.get('results', []))}")
    for r in result.get("results", [])[:2]:
        print(f"    - {r.get('title', '')[:60]}")

    assert "error" not in result
    assert len(result.get("results", [])) > 0
    print("[PASS] web_search returned results")


def test_web_scrape():
    """Test web_scrape extracts content from a URL."""
    print("\n=== Test: web_scrape ===")

    result = json.loads(global_registry.execute("web_scrape", {
        "url": "https://www.databricks.com/company/careers",
    }))

    print(f"  URL: {result.get('url')}")
    print(f"  Title: {result.get('title', '')[:60]}")
    print(f"  Content length: {result.get('length', 0)} chars")

    assert result.get("content")
    assert result.get("length", 0) > 100
    print("[PASS] web_scrape extracted content")


def test_web_scrape_linkedin_blocked():
    """Test that LinkedIn scraping is blocked."""
    print("\n=== Test: web_scrape LinkedIn blocked ===")

    result = json.loads(global_registry.execute("web_scrape", {
        "url": "https://www.linkedin.com/in/someone",
    }))

    print(f"  Error: {result.get('error', '')[:60]}")
    assert "prohibited" in result.get("error", "").lower() or "violation" in result.get("error", "").lower()
    print("[PASS] LinkedIn scraping correctly blocked")


if __name__ == "__main__":
    tests = [test_web_search, test_web_scrape, test_web_scrape_linkedin_blocked]
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
        print("All Step 3 tests PASSED!")
