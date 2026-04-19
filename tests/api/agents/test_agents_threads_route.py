"""Tests for thread state inspection endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI
from httpx._transports.asgi import ASGITransport

from src.api.agents.agents_threads_route import _serialise_state, router


@pytest.fixture()
def asgi_app():
    app = FastAPI()
    app.include_router(router)
    return app


# --- _serialise_state helper (sync) ---


def test_serialise_state_none_returns_empty_response():
    result = _serialise_state(None)
    assert result.values is None
    assert result.next == []
    assert result.tasks == []


def test_serialise_state_with_snapshot_object():
    snapshot = MagicMock()
    snapshot.values = {"key": "val"}
    snapshot.next = ["node_a"]
    snapshot.tasks = [{"id": "1"}]
    result = _serialise_state(snapshot)
    assert result.values == {"key": "val"}
    assert result.next == ["node_a"]
    assert result.tasks == [{"id": "1"}]


def test_serialise_state_tasks_as_non_dict_are_stringified():
    snapshot = MagicMock()
    snapshot.values = {}
    snapshot.next = []
    snapshot.tasks = ["task-id-1"]
    result = _serialise_state(snapshot)
    assert result.tasks == [{"id": "task-id-1"}]


# --- GET /{app_name}/threads/{thread_id} ---


@pytest.mark.asyncio
async def test_get_thread_state_returns_200(asgi_app):
    mock_app = AsyncMock()
    mock_app.aget_state.return_value = None
    with patch("src.api.agents.agents_threads_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/supervisor/threads/t1")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_thread_state_none_values(asgi_app):
    mock_app = AsyncMock()
    mock_app.aget_state.return_value = None
    with patch("src.api.agents.agents_threads_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/supervisor/threads/t1")
    data = response.json()
    assert data["values"] is None
    assert data["next"] == []
    assert data["tasks"] == []


@pytest.mark.asyncio
async def test_get_thread_state_with_values(asgi_app):
    snapshot = MagicMock()
    snapshot.values = {"messages": ["hello"]}
    snapshot.next = ["agent"]
    snapshot.tasks = []
    mock_app = AsyncMock()
    mock_app.aget_state.return_value = snapshot
    with patch("src.api.agents.agents_threads_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/supervisor/threads/t1")
    data = response.json()
    assert data["values"] == {"messages": ["hello"]}
    assert data["next"] == ["agent"]


@pytest.mark.asyncio
async def test_get_thread_state_passes_thread_id_in_config(asgi_app):
    mock_app = AsyncMock()
    mock_app.aget_state.return_value = None
    with patch("src.api.agents.agents_threads_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            await client.get("/supervisor/threads/my-thread")
    call_kwargs = mock_app.aget_state.call_args[1]
    assert call_kwargs["config"]["configurable"]["thread_id"] == "my-thread"


@pytest.mark.asyncio
async def test_get_thread_state_returns_404_for_unknown_app(asgi_app):
    from fastapi import HTTPException

    with patch(
        "src.api.agents.agents_threads_route.get_app",
        side_effect=HTTPException(status_code=404, detail="Unknown app"),
    ):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/unknown/threads/t1")
    assert response.status_code == 404


# --- GET /{app_name}/threads/{thread_id}/history ---


@pytest.mark.asyncio
async def test_get_thread_history_returns_200(asgi_app):
    mock_app = MagicMock()

    async def _empty_history(**_kwargs):
        return
        yield

    mock_app.aget_state_history.return_value = _empty_history()
    with patch("src.api.agents.agents_threads_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/supervisor/threads/t1/history")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_thread_history_returns_list(asgi_app):
    mock_app = MagicMock()

    async def _empty_history(**_kwargs):
        return
        yield

    mock_app.aget_state_history.return_value = _empty_history()
    with patch("src.api.agents.agents_threads_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/supervisor/threads/t1/history")
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_thread_history_returns_snapshots(asgi_app):
    snapshot = MagicMock()
    snapshot.values = {"step": 1}
    snapshot.next = []
    snapshot.tasks = []

    mock_app = MagicMock()

    async def _history(**_kwargs):
        yield snapshot

    mock_app.aget_state_history.return_value = _history()
    with patch("src.api.agents.agents_threads_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/supervisor/threads/t1/history")
    data = response.json()
    assert len(data) == 1
    assert data[0]["values"] == {"step": 1}
