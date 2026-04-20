"""Tests for POST /{app_name}/stream SSE route."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI
from httpx._transports.asgi import ASGITransport

from src.api.agents.stream_route import _event_generator, router

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _collect(gen) -> list[str]:
    """Drain an async generator into a list."""
    results = []
    async for item in gen:
        results.append(item)
    return results


def _parse_events(lines: list[str]) -> list[dict]:
    events = []
    for line in lines:
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: "):]))
    return events


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def asgi_app():
    app = FastAPI()
    app.include_router(router)
    return app


# ---------------------------------------------------------------------------
# _event_generator unit tests
# ---------------------------------------------------------------------------


async def test_event_generator_emits_done_for_empty_stream():
    mock_app = MagicMock()

    async def _empty():
        return
        yield  # make it an async generator

    mock_app.astream.return_value = _empty()
    lines = await _collect(_event_generator(mock_app, [], "t1"))
    events = _parse_events(lines)
    assert events[-1]["type"] == "done"


async def test_event_generator_emits_token_for_ai_message_chunk():
    from langchain_core.messages import AIMessageChunk

    mock_app = MagicMock()
    chunk = AIMessageChunk(content="hello")
    metadata = {"langgraph_node": "agent"}

    async def _stream():
        yield chunk, metadata

    mock_app.astream.return_value = _stream()
    lines = await _collect(_event_generator(mock_app, [], "t1"))
    events = _parse_events(lines)
    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) == 1
    assert token_events[0]["content"] == "hello"
    assert token_events[0]["node"] == "agent"


async def test_event_generator_emits_message_for_generic_chunk():
    mock_app = MagicMock()

    class GenericChunk:
        content = "generic"

    async def _stream():
        yield GenericChunk(), {"langgraph_node": "writer"}

    mock_app.astream.return_value = _stream()
    lines = await _collect(_event_generator(mock_app, [], "t1"))
    events = _parse_events(lines)
    msg_events = [e for e in events if e["type"] == "message"]
    assert len(msg_events) == 1
    assert msg_events[0]["content"] == "generic"


async def test_event_generator_emits_error_on_exception():
    mock_app = MagicMock()

    async def _failing():
        raise RuntimeError("boom")
        yield  # make it an async generator

    mock_app.astream.return_value = _failing()
    lines = await _collect(_event_generator(mock_app, [], "t1"))
    events = _parse_events(lines)
    assert events[0]["type"] == "error"
    # Error content is sanitised — the real exception is only logged server-side.
    assert events[0]["content"] == "Internal stream error"


async def test_event_generator_skips_chunk_without_content():
    mock_app = MagicMock()

    class NoContent:
        pass

    async def _stream():
        yield NoContent(), {}

    mock_app.astream.return_value = _stream()
    lines = await _collect(_event_generator(mock_app, [], "t1"))
    events = _parse_events(lines)
    assert all(e["type"] in ("done",) for e in events)


# ---------------------------------------------------------------------------
# HTTP endpoint tests
# ---------------------------------------------------------------------------


async def test_stream_response_content_type_is_event_stream(asgi_app):
    mock_app = MagicMock()

    async def _empty():
        return
        yield

    mock_app.astream.return_value = _empty()
    with patch("src.api.agents.stream_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/supervisor/stream",
                json={"messages": [], "thread_id": "t1"},
            )
    assert "text/event-stream" in response.headers["content-type"]


async def test_stream_returns_404_for_unknown_app(asgi_app):
    from fastapi import HTTPException

    with patch(
        "src.api.agents.stream_route.get_app",
        side_effect=HTTPException(status_code=404, detail="Unknown app"),
    ):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/unknown/stream",
                json={"messages": [], "thread_id": "t1"},
            )
    assert response.status_code == 404
