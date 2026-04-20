"""Tests for POST /{app_name}/invoke route."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI
from httpx._transports.asgi import ASGITransport

from src.api.agents.invoke_route import _last_message_content, router


@pytest.fixture()
def asgi_app():
    app = FastAPI()
    app.include_router(router)
    return app


# --- _last_message_content helper (sync) ---


def test_last_message_content_empty_list():
    assert _last_message_content([]) is None


def test_last_message_content_dict_message():
    messages = [{"role": "user", "content": "hi"}, {"role": "ai", "content": "hello"}]
    assert _last_message_content(messages) == "hello"


def test_last_message_content_object_message():
    class Msg:
        content = "from object"

    assert _last_message_content([Msg()]) == "from object"


def test_last_message_content_dict_without_content_key():
    assert _last_message_content([{"role": "ai"}]) is None


# --- invoke route ---


@pytest.mark.asyncio
async def test_invoke_returns_200_with_mocked_app(asgi_app):
    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {
        "messages": [{"role": "ai", "content": "done"}]
    }
    payload = {"messages": [{"role": "user", "content": "hi"}], "thread_id": "t1"}
    with patch("src.api.agents.invoke_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post("/supervisor/invoke", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invoke_response_contains_messages(asgi_app):
    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {
        "messages": [{"role": "ai", "content": "result"}]
    }
    with patch("src.api.agents.invoke_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/supervisor/invoke",
                json={"messages": [], "thread_id": "t1"},
            )
    assert "messages" in response.json()


@pytest.mark.asyncio
async def test_invoke_response_last_message_extracted(asgi_app):
    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {
        "messages": [{"role": "ai", "content": "final answer"}]
    }
    with patch("src.api.agents.invoke_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/supervisor/invoke",
                json={"messages": [], "thread_id": "t1"},
            )
    assert response.json()["last_message"] == "final answer"


@pytest.mark.asyncio
async def test_invoke_response_structured_response_none_by_default(asgi_app):
    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {"messages": []}
    with patch("src.api.agents.invoke_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/supervisor/invoke",
                json={"messages": [], "thread_id": "t1"},
            )
    assert response.json()["structured_response"] is None


@pytest.mark.asyncio
async def test_invoke_calls_ainvoke_with_thread_id(asgi_app):
    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {"messages": []}
    with patch("src.api.agents.invoke_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            await client.post(
                "/supervisor/invoke",
                json={"messages": [], "thread_id": "my-thread"},
            )
    call_kwargs = mock_app.ainvoke.call_args[1]
    assert call_kwargs["config"]["configurable"]["thread_id"] == "my-thread"


@pytest.mark.asyncio
async def test_invoke_returns_404_for_unknown_app(asgi_app):
    from fastapi import HTTPException

    with patch(
        "src.api.agents.invoke_route.get_app",
        side_effect=HTTPException(status_code=404, detail="Unknown app"),
    ):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/unknown_app/invoke",
                json={"messages": [], "thread_id": "t1"},
            )
    assert response.status_code == 404
