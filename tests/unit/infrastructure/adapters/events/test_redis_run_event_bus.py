"""Unit tests for RedisRunEventBus — mocked Redis client, no live server."""

import json
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.infrastructure.adapters.events.redis_run_event_bus import RedisRunEventBus


@pytest.fixture
def run_id():
    return uuid4()


@pytest.mark.asyncio
async def test_publish_sends_json_to_redis_channel(run_id):
    mock_client = AsyncMock()
    bus = object.__new__(RedisRunEventBus)
    bus._client = mock_client

    await bus.publish(run_id, {"type": "assistant", "text": "hello"})

    mock_client.publish.assert_awaited_once_with(
        f"run:{run_id}:events",
        json.dumps({"type": "assistant", "text": "hello"}),
    )


@pytest.mark.asyncio
async def test_publish_is_noop_when_client_is_none(run_id):
    bus = RedisRunEventBus(redis_url=None)
    # Must not raise
    await bus.publish(run_id, {"type": "test"})


def test_init_creates_no_client_for_memory_url():
    bus = RedisRunEventBus(redis_url="memory://")
    assert bus._client is None


def test_init_creates_no_client_when_url_is_none():
    bus = RedisRunEventBus(redis_url=None)
    assert bus._client is None


def test_channel_name_includes_run_id(run_id):
    bus = RedisRunEventBus(redis_url=None)
    assert bus._channel(run_id) == f"run:{run_id}:events"


@pytest.mark.asyncio
async def test_subscribe_yields_events_and_stops_at_sentinel(run_id):
    """subscribe yields events up to and including _stream_done, then stops."""

    async def _fake_listen() -> AsyncGenerator:
        # subscription confirmation message (must be skipped)
        yield {"type": "subscribe", "data": 1}
        yield {"type": "message", "data": json.dumps({"type": "text", "text": "hi"})}
        yield {"type": "message", "data": json.dumps({"type": "_stream_done"})}
        # this must never be reached
        yield {"type": "message", "data": json.dumps({"type": "extra"})}

    pubsub = AsyncMock()
    pubsub.listen = _fake_listen
    pubsub.unsubscribe = AsyncMock()

    mock_client = MagicMock()
    mock_client.pubsub.return_value = pubsub

    bus = object.__new__(RedisRunEventBus)
    bus._client = mock_client

    collected = []
    async for event in bus.subscribe(run_id):
        collected.append(event)

    assert collected == [
        {"type": "text", "text": "hi"},
        {"type": "_stream_done"},
    ]
    pubsub.unsubscribe.assert_awaited_once_with(f"run:{run_id}:events")


@pytest.mark.asyncio
async def test_subscribe_is_noop_when_client_is_none(run_id):
    bus = RedisRunEventBus(redis_url=None)
    events = [e async for e in bus.subscribe(run_id)]
    assert events == []
