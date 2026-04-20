"""Tests for POST /{app_name}/resume route."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI
from httpx._transports.asgi import ASGITransport

from src.api.agents.resume_route import router

pytestmark = pytest.mark.asyncio


@pytest.fixture()
def asgi_app():
    app = FastAPI()
    app.include_router(router)
    return app


async def test_resume_returns_200_with_mocked_app(asgi_app):
    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {
        "messages": [{"role": "ai", "content": "resumed"}]
    }
    with patch("src.api.agents.resume_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/interrupt/resume",
                json={"thread_id": "t1", "decision": "approve"},
            )
    assert response.status_code == 200


async def test_resume_response_contains_messages(asgi_app):
    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {
        "messages": [{"role": "ai", "content": "done"}]
    }
    with patch("src.api.agents.resume_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/interrupt/resume",
                json={"thread_id": "t1", "decision": "approve"},
            )
    assert "messages" in response.json()


async def test_resume_last_message_extracted(asgi_app):
    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {
        "messages": [{"role": "ai", "content": "final"}]
    }
    with patch("src.api.agents.resume_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/interrupt/resume",
                json={"thread_id": "t1", "decision": "approve"},
            )
    assert response.json()["last_message"] == "final"


async def test_resume_calls_ainvoke_with_command(asgi_app):
    from langgraph.types import Command

    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {"messages": []}
    with patch("src.api.agents.resume_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            await client.post(
                "/interrupt/resume",
                json={"thread_id": "t1", "decision": "approve"},
            )
    call_args = mock_app.ainvoke.call_args
    command = call_args[0][0]
    assert isinstance(command, Command)
    assert command.resume == "approve"


async def test_resume_passes_thread_id_in_config(asgi_app):
    mock_app = AsyncMock()
    mock_app.ainvoke.return_value = {"messages": []}
    with patch("src.api.agents.resume_route.get_app", return_value=mock_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            await client.post(
                "/interrupt/resume",
                json={"thread_id": "my-thread", "decision": "reject"},
            )
    call_kwargs = mock_app.ainvoke.call_args[1]
    assert call_kwargs["config"]["configurable"]["thread_id"] == "my-thread"


async def test_resume_missing_decision_returns_422(asgi_app):
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/interrupt/resume",
            json={"thread_id": "t1"},
        )
    assert response.status_code == 422


async def test_resume_returns_404_for_unknown_app(asgi_app):
    from fastapi import HTTPException

    with patch(
        "src.api.agents.resume_route.get_app",
        side_effect=HTTPException(status_code=404, detail="Unknown app"),
    ):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/unknown/resume",
                json={"thread_id": "t1", "decision": "approve"},
            )
    assert response.status_code == 404
