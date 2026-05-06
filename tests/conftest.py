"""Shared test fixtures — async SQLite engine, session, and dependency override."""

import pytest
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.persistence.base import Base
import src.adapters.persistence.user.model  # noqa: F401 — registers UserModel with Base
from src.main import create_app

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(async_engine):
    """AsyncClient with the container's db_session_factory overridden to use SQLite."""
    test_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    app = create_app()
    app.container.core.db_session_factory.override(  # type: ignore[attr-defined]
        providers.Object(test_session_factory)
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.container.core.db_session_factory.reset_override()  # type: ignore[attr-defined]
