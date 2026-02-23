"""Web scraping tool -- httpx + BeautifulSoup.

Note on LinkedIn: Direct scraping is prohibited (ToS violation).
Only Google-indexed public info via web_search is allowed.
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from tools.registry import register_tool


@register_tool(
    name="web_scrape",
    description="Fetch and extract text content from a given URL. Do NOT use on LinkedIn URLs (ToS violation).",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to scrape"},
        },
        "required": ["url"],
    },
)
def web_scrape(url: str) -> dict:
    """Fetch a URL and extract clean text content."""

    # Block LinkedIn direct scraping
    if "linkedin.com" in url:
        return {
            "error": "LinkedIn direct scraping is prohibited (ToS violation). "
            "Use web_search with 'site:linkedin.com' for public info instead.",
            "url": url,
            "content": "",
        }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    response = httpx.get(url, headers=headers, follow_redirects=True, timeout=15.0)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script, style, nav, footer, header tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Extract text
    text = soup.get_text(separator="\n", strip=True)

    # Trim excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)

    # Truncate if too long (LLM context limit)
    max_chars = 15000
    if len(clean_text) > max_chars:
        clean_text = clean_text[:max_chars] + "\n\n[... truncated]"

    return {
        "url": url,
        "title": soup.title.string if soup.title else "",
        "content": clean_text,
        "length": len(clean_text),
    }
