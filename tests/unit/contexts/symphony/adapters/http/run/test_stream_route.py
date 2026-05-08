"""Unit tests for the SSE stream route generator logic."""

import json
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest

from src.contexts.symphony.adapters.http.run.routes.stream import _build_sse_generator
from src.infrastructure.adapters.events.redis_run_event_bus import RedisRunEventBus


class _FakeBus:
    """Fake bus that replays a fixed sequence of events."""

    def __init__(self, events: list[dict]) -> None:
        self._events = events

    async def subscribe(self, run_id) -> AsyncGenerator[dict, None]:
        for event in self._events:
            yield event


@pytest.mark.asyncio
async def test_generator_yields_sse_formatted_events():
    """Each event becomes a properly formatted SSE data line."""
    bus = _FakeBus([
        {"type": "text", "text": "hello"},
        {"type": "_stream_done"},
    ])
    run_id = uuid4()

    chunks = []
    async for chunk in _build_sse_generator(run_id, bus):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0] == f"data: {json.dumps({'type': 'text', 'text': 'hello'})}\n\n"
    assert chunks[1] == f"data: {json.dumps({'type': '_stream_done'})}\n\n"


@pytest.mark.asyncio
async def test_generator_stops_after_stream_done():
    """Generator does not yield events after _stream_done."""
    bus = _FakeBus([
        {"type": "text", "text": "a"},
        {"type": "_stream_done"},
        {"type": "text", "text": "should not appear"},
    ])
    run_id = uuid4()

    chunks = [c async for c in _build_sse_generator(run_id, bus)]

    types = [json.loads(c.removeprefix("data: ").strip()).get("type") for c in chunks]
    assert "should not appear" not in str(types)
    assert "_stream_done" in types


@pytest.mark.asyncio
async def test_generator_empty_when_bus_has_no_client():
    """Bus with no Redis client yields nothing; generator exits cleanly."""
    bus = RedisRunEventBus(redis_url=None)
    run_id = uuid4()

    chunks = [c async for c in _build_sse_generator(run_id, bus)]
    assert chunks == []
