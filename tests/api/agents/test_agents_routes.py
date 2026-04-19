"""Tests for the assembled agents router."""

from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI
from httpx._transports.asgi import ASGITransport

import src.api.agents.agents_dependencies as deps
from src.api.agents.agents_routes import agents_router

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def reset_registry():
    deps._apps.clear()
    deps._mcp_tools.clear()
    yield
    deps._apps.clear()
    deps._mcp_tools.clear()


@pytest.fixture()
def asgi_app():
    app = FastAPI()
    app.include_router(agents_router)
    return app


async def test_assembled_router_health_returns_200(asgi_app):
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200


async def test_assembled_router_health_status_ok(asgi_app):
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
    assert response.json()["status"] == "ok"


async def test_assembled_router_health_reflects_registered_apps(asgi_app):
    deps._apps["supervisor"] = object()
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
    assert "supervisor" in response.json()["apps"]


async def test_assembled_router_includes_invoke_route(asgi_app):
    """POST /{app_name}/invoke must be reachable (404 from registry, not 405)."""
    from fastapi import HTTPException

    with patch(
        "src.api.agents.agents_invoke_route.get_app",
        side_effect=HTTPException(status_code=404, detail="not found"),
    ):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/supervisor/invoke",
                json={"messages": [], "thread_id": "t1"},
            )
    assert response.status_code == 404


async def test_assembled_router_includes_stream_route(asgi_app):
    """POST /{app_name}/stream must be reachable."""
    from fastapi import HTTPException

    with patch(
        "src.api.agents.agents_stream_route.get_app",
        side_effect=HTTPException(status_code=404, detail="not found"),
    ):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/supervisor/stream",
                json={"messages": [], "thread_id": "t1"},
            )
    assert response.status_code == 404


async def test_assembled_router_includes_resume_route(asgi_app):
    """POST /{app_name}/resume must be reachable."""
    from fastapi import HTTPException

    with patch(
        "src.api.agents.agents_resume_route.get_app",
        side_effect=HTTPException(status_code=404, detail="not found"),
    ):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/supervisor/resume",
                json={"thread_id": "t1", "decision": "approve"},
            )
    assert response.status_code == 404


async def test_assembled_router_includes_threads_route(asgi_app):
    """GET /{app_name}/threads/{thread_id} must be reachable."""
    from fastapi import HTTPException

    with patch(
        "src.api.agents.agents_threads_route.get_app",
        side_effect=HTTPException(status_code=404, detail="not found"),
    ):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=asgi_app), base_url="http://testserver"
        ) as client:
            response = await client.get("/supervisor/threads/t1")
    assert response.status_code == 404
