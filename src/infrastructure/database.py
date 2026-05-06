"""Async SQLAlchemy session helper and DB initialisation."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.infrastructure.adapters.persistence import registry  # noqa: F401 — triggers model registration
from src.infrastructure.adapters.persistence.base import Base
from src.infrastructure.containers import get_container


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a per-request AsyncSession from the container's session factory.

    The session factory is a Singleton owned by the DI container stored in
    app.state.container (request.app.state.container.core.db_session_factory).
    This keeps the session scoped to the HTTP request while the engine and
    factory remain long-lived singletons.
    """
    factory: async_sessionmaker[AsyncSession] = get_container(
        request
    ).core.db_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db(engine: AsyncEngine) -> None:
    """Create all tables — used in development and test environments."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
