"""Tests for GET /health agents route."""

import pytest
import httpx
from httpx._transports.asgi import ASGITransport
from fastapi import FastAPI

import src.api.agents.agents_dependencies as deps
from src.api.agents.agents_health_route import router

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
    app.include_router(router)
    return app


async def test_health_returns_200(asgi_app):
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200


async def test_health_status_is_ok(asgi_app):
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
    assert response.json()["status"] == "ok"


async def test_health_apps_empty_when_no_registry(asgi_app):
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
    assert response.json()["apps"] == []


async def test_health_apps_lists_registered_apps(asgi_app):
    deps._apps["supervisor"] = object()
    deps._apps["swarm"] = object()
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
    assert set(response.json()["apps"]) == {"supervisor", "swarm"}


async def test_health_mcp_tools_loaded_zero_when_empty(asgi_app):
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
    assert response.json()["mcp_tools_loaded"] == 0


async def test_health_mcp_tools_loaded_reflects_count(asgi_app):
    deps._mcp_tools.extend(["t1", "t2"])
    async with httpx.AsyncClient(
        transport=ASGITransport(app=asgi_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
    assert response.json()["mcp_tools_loaded"] == 2
