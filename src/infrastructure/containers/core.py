"""Core container — cross-cutting infrastructure providers.

Owns settings, async DB engine, and the session factory. These are shared
by every aggregate container and are kept here so a new bounded context
never has to redeclare them.
"""

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.infrastructure.config import get_settings


class CoreContainer(containers.DeclarativeContainer):
    config = providers.Singleton(get_settings)

    db_engine = providers.Singleton(
        create_async_engine,
        url=config.provided.DATABASE_URL,
        future=True,
        echo=False,
    )

    db_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=db_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    event_publisher = providers.Singleton(InMemoryEventPublisher)
