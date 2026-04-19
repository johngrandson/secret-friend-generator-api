"""Integration smoke test: agents router wired correctly with all 7 apps."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI
from httpx._transports.asgi import ASGITransport

pytestmark = pytest.mark.asyncio

_ALL_APP_NAMES = [
    "supervisor",
    "swarm",
    "interrupt",
    "analyst",
    "researcher",
    "rag",
    "support",
]


async def test_health_lists_all_seven_apps():
    apps = {name: MagicMock() for name in _ALL_APP_NAMES}
    with patch("src.api.agents.agents_dependencies._apps", apps):
        with patch("src.api.agents.agents_dependencies._mcp_tools", []):
            from src.api.agents.agents_routes import agents_router

            app = FastAPI()
            app.include_router(agents_router, prefix="/agents")

            async with httpx.AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/agents/health")

            assert response.status_code == 200
            data = response.json()
            assert len(data["apps"]) == 7
            for name in _ALL_APP_NAMES:
                assert name in data["apps"]
