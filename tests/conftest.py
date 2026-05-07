"""Shared test fixtures — async SQLite engine, session, fake UoWs, and HTTP client."""

import pytest
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock

from src.infrastructure.adapters.persistence import registry  # noqa: F401 — triggers model registration
from src.infrastructure.adapters.persistence.base import Base
from src.shared.events import DomainEvent
from src.infrastructure.containers import get_container_from_app
from src.main import create_app


class FakePublisher:
    """In-memory IEventPublisher impl for tests. Accumulates published events.

    Implements IEventPublisher structurally — no inheritance required.
    Use the `published` list to assert what came through.
    """

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class FakeIdentityUoW:
    """Fake IIdentityUnitOfWork for identity use case unit tests.

    Exposes `users` as an AsyncMock repo and tracks commit/rollback calls.
    Use `uow.committed` and `uow.rolled_back` in assertions.
    """

    def __init__(self) -> None:
        self.users = AsyncMock()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> "FakeIdentityUoW":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


class FakeSymphonyUoW:
    """Fake ISymphonyUnitOfWork for symphony use case unit tests.

    Exposes `runs`, `specs`, `plans`, `agent_sessions`, `pull_requests`
    as AsyncMock repos and tracks commit/rollback calls via
    `uow.committed` and `uow.rolled_back`.
    """

    def __init__(self) -> None:
        self.runs = AsyncMock()
        self.specs = AsyncMock()
        self.plans = AsyncMock()
        self.agent_sessions = AsyncMock()
        self.pull_requests = AsyncMock()
        self.gate_results = AsyncMock()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> "FakeSymphonyUoW":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_engine():
    """Per-test SQLite in-memory engine — each test gets a fresh DB.

    Function-scoped to prevent state leak between tests: the UoW commit
    persists changes, so a session rollback alone won't undo them.
    A fresh engine = fresh tables.
    """
    engine = create_async_engine(TEST_DB_URL, echo=False)
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
def fake_publisher() -> FakePublisher:
    """Fresh FakePublisher per test — assert against `.published`."""
    return FakePublisher()


@pytest.fixture
def fake_identity_uow() -> FakeIdentityUoW:
    """Fresh FakeIdentityUoW per test with mocked `users` repo."""
    return FakeIdentityUoW()


@pytest.fixture
def fake_symphony_uow() -> FakeSymphonyUoW:
    """Fresh FakeSymphonyUoW per test with mocked `runs`, `specs`, `plans` repos."""
    return FakeSymphonyUoW()


@pytest.fixture
async def client(async_engine):
    """AsyncClient with the container's db_session_factory overridden to use SQLite."""
    test_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    app = create_app()
    container = get_container_from_app(app)
    container.core.db_session_factory.override(providers.Object(test_session_factory))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    container.core.db_session_factory.reset_override()
