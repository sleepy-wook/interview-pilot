"""Web search tool -- DuckDuckGo (no API key required)."""

from __future__ import annotations

from ddgs import DDGS

from tools.registry import register_tool


@register_tool(
    name="web_search",
    description="Search the web for information. Returns top results with title, URL, and snippet.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query string"},
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (default: 5, max: 10)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
)
def web_search(query: str, num_results: int = 5) -> dict:
    """Search using DuckDuckGo."""
    num_results = min(num_results, 10)

    with DDGS() as ddgs:
        raw = list(ddgs.text(query, max_results=num_results))

    results = []
    for item in raw:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("href", ""),
            "snippet": item.get("body", ""),
        })

    return {
        "query": query,
        "total_results": str(len(results)),
        "results": results,
    }
