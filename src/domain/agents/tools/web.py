import re
from typing import Any

import httpx
from langchain_core.tools import tool

_DDGS_URL = "https://api.duckduckgo.com/"


@tool
async def web_search(query: str) -> str:
    """Search the web using DuckDuckGo instant answer API.

    Args:
        query: Search query string.

    Returns:
        Abstract text and related topics from DuckDuckGo.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            _DDGS_URL,
            params={"q": query, "format": "json", "no_html": "1"},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()

    parts: list[str] = []

    abstract = data.get("AbstractText", "")
    if abstract:
        parts.append(abstract)

    for topic in data.get("RelatedTopics", []):
        if isinstance(topic, dict):
            text = topic.get("Text", "")
            if text:
                parts.append(text)

    return "\n".join(parts) if parts else "No results found."


@tool
async def scrape_url(url: str) -> str:
    """Fetch a URL and return its text content with HTML tags stripped.

    Args:
        url: The URL to fetch.

    Returns:
        Plain text content (first 4000 characters).
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text

    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:4000]
