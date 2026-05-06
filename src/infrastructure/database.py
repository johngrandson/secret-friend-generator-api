"""Async SQLAlchemy session helper and DB initialisation."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.adapters.persistence.base import Base
import src.adapters.persistence.user.model  # noqa: F401 — registers UserModel with Base


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a per-request AsyncSession from the container's session factory.

    The session factory is a Singleton owned by the DI container attached to
    the running FastAPI application (request.app.container.db_session_factory).
    This keeps the session scoped to the HTTP request while the engine and
    factory remain long-lived singletons.
    """
    session_factory = request.app.container.core.db_session_factory()
    async with session_factory() as session:
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
