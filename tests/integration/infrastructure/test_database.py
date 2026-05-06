"""Integration test for init_db — bootstraps schema on a fresh in-memory engine."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

import src.infrastructure.adapters.persistence.registry  # noqa: F401 — register all models
from src.infrastructure.adapters.persistence.base import Base
from src.infrastructure.database import init_db


@pytest.mark.asyncio
async def test_init_db_creates_all_tables() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    try:
        await init_db(engine)
        async with engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: list(Base.metadata.tables.keys())
            )
        assert "users" in tables
        assert "symphony_runs" in tables
    finally:
        await engine.dispose()
