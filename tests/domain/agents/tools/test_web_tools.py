from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.domain.agents.tools.web_tools as mod


def _make_json_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


def _make_text_response(text: str) -> MagicMock:
    response = MagicMock()
    response.text = text
    return response


@pytest.mark.asyncio
async def test_web_search_returns_abstract_text() -> None:
    payload = {
        "AbstractText": "Python is a programming language.",
        "RelatedTopics": [],
    }
    mock_get = AsyncMock(return_value=_make_json_response(payload))
    with patch("httpx.AsyncClient.get", mock_get):
        result = await mod.web_search.ainvoke({"query": "Python"})
    assert "Python is a programming language." in result


@pytest.mark.asyncio
async def test_web_search_includes_related_topics() -> None:
    payload = {
        "AbstractText": "",
        "RelatedTopics": [
            {"Text": "Topic A about Python"},
            {"Text": "Topic B about scripting"},
        ],
    }
    mock_get = AsyncMock(return_value=_make_json_response(payload))
    with patch("httpx.AsyncClient.get", mock_get):
        result = await mod.web_search.ainvoke({"query": "Python"})
    assert "Topic A about Python" in result
    assert "Topic B about scripting" in result


@pytest.mark.asyncio
async def test_web_search_no_results() -> None:
    payload = {"AbstractText": "", "RelatedTopics": []}
    mock_get = AsyncMock(return_value=_make_json_response(payload))
    with patch("httpx.AsyncClient.get", mock_get):
        result = await mod.web_search.ainvoke({"query": "xyzzy"})
    assert result == "No results found."


@pytest.mark.asyncio
async def test_web_search_skips_non_dict_topics() -> None:
    payload = {
        "AbstractText": "Main text.",
        "RelatedTopics": [
            ["nested", "list"],
            {"Text": "Valid topic"},
        ],
    }
    mock_get = AsyncMock(return_value=_make_json_response(payload))
    with patch("httpx.AsyncClient.get", mock_get):
        result = await mod.web_search.ainvoke({"query": "test"})
    assert "Main text." in result
    assert "Valid topic" in result


@pytest.mark.asyncio
async def test_scrape_url_strips_html_tags() -> None:
    html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
    mock_get = AsyncMock(return_value=_make_text_response(html))
    with patch("httpx.AsyncClient.get", mock_get):
        result = await mod.scrape_url.ainvoke({"url": "http://example.com"})
    assert "<h1>" not in result
    assert "<p>" not in result
    assert "Hello" in result
    assert "World" in result


@pytest.mark.asyncio
async def test_scrape_url_truncates_to_4000_chars() -> None:
    long_text = "A" * 8000
    html = f"<p>{long_text}</p>"
    mock_get = AsyncMock(return_value=_make_text_response(html))
    with patch("httpx.AsyncClient.get", mock_get):
        result = await mod.scrape_url.ainvoke({"url": "http://example.com"})
    assert len(result) <= 4000


@pytest.mark.asyncio
async def test_scrape_url_collapses_whitespace() -> None:
    html = "<p>too   many    spaces</p>"
    mock_get = AsyncMock(return_value=_make_text_response(html))
    with patch("httpx.AsyncClient.get", mock_get):
        result = await mod.scrape_url.ainvoke({"url": "http://example.com"})
    assert "  " not in result
