"""Smoke test: full app boot via create_app() lifespan + router registration.

Verifies that the DI graph wires correctly, the lifespan runs without error,
all expected route prefixes are registered, and /openapi.json is served.
Uses the same db_session_factory override pattern as the shared `client` fixture
in conftest.py — providers.Object wrapping a test-scoped async_sessionmaker.
"""

import pytest
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.infrastructure.containers import get_container_from_app
from src.main import create_app


@pytest.mark.asyncio
async def test_app_starts_and_serves_openapi(async_engine) -> None:
    """Boot the full DI graph with a test DB override; /openapi.json must return 200."""
    app = create_app()
    container = get_container_from_app(app)
    test_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    container.core.db_session_factory.override(providers.Object(test_session_factory))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/openapi.json")

    container.core.db_session_factory.reset_override()

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema_contains_expected_route_prefixes(async_engine) -> None:
    """All four resource route groups must appear in the OpenAPI path registry."""
    app = create_app()
    container = get_container_from_app(app)
    test_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    container.core.db_session_factory.override(providers.Object(test_session_factory))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/openapi.json")

    container.core.db_session_factory.reset_override()

    paths = resp.json()["paths"]
    path_keys = "\n".join(paths.keys())

    assert "/users/" in path_keys, f"Expected /users/ routes, got: {list(paths)[:10]}"
    assert "/runs/" in path_keys, f"Expected /runs/ routes, got: {list(paths)[:10]}"
    assert "/specs/" in path_keys, f"Expected /specs/ routes, got: {list(paths)[:10]}"
    assert "/plans/" in path_keys, f"Expected /plans/ routes, got: {list(paths)[:10]}"


@pytest.mark.asyncio
async def test_container_attached_to_app_state(async_engine) -> None:
    """Container must be stored on app.state so request-scoped helpers can retrieve it."""
    app = create_app()
    container = get_container_from_app(app)
    test_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    container.core.db_session_factory.override(providers.Object(test_session_factory))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test"):
        retrieved = get_container_from_app(app)

    container.core.db_session_factory.reset_override()

    assert retrieved is container
