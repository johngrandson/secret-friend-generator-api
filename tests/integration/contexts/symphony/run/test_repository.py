"""Integration tests for SQLAlchemyRunRepository against SQLite in-memory."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.contexts.symphony.adapters.persistence.run.repository import SQLAlchemyRunRepository
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus


def _make_run(issue_id: str = "ISSUE-1") -> Run:
    return Run.create(issue_id=issue_id)


async def test_save_and_find_by_id(async_session):
    repo = SQLAlchemyRunRepository(async_session)
    run = _make_run()

    saved = await repo.save(run)
    found = await repo.find_by_id(saved.id)

    assert found is not None
    assert found.id == saved.id
    assert found.issue_id == "ISSUE-1"


async def test_find_by_id_returns_none_when_missing(async_session):
    repo = SQLAlchemyRunRepository(async_session)

    result = await repo.find_by_id(uuid4())

    assert result is None


async def test_list_paginates(async_session):
    repo = SQLAlchemyRunRepository(async_session)
    for i in range(5):
        await repo.save(_make_run(f"ISSUE-{i}"))

    page1 = await repo.list(limit=2, offset=0)
    page2 = await repo.list(limit=2, offset=2)

    assert len(page1) == 2
    assert len(page2) == 2
    assert {r.issue_id for r in page1}.isdisjoint({r.issue_id for r in page2})


async def test_update_persists(async_session):
    repo = SQLAlchemyRunRepository(async_session)
    run = _make_run()
    saved = await repo.save(run)

    saved.set_status(RunStatus.GEN_SPEC)
    updated = await repo.update(saved)

    assert updated.status == RunStatus.GEN_SPEC


async def test_delete(async_session):
    repo = SQLAlchemyRunRepository(async_session)
    run = _make_run()
    saved = await repo.save(run)

    deleted = await repo.delete(saved.id)
    found = await repo.find_by_id(saved.id)

    assert deleted is True
    assert found is None


async def test_delete_nonexistent_returns_false(async_session):
    repo = SQLAlchemyRunRepository(async_session)

    result = await repo.delete(uuid4())

    assert result is False


async def test_find_due_retries(async_session):
    repo = SQLAlchemyRunRepository(async_session)
    now = datetime.now(timezone.utc)

    # Run due for retry
    due_run = Run(
        issue_id="ISSUE-DUE",
        status=RunStatus.RETRY_PENDING,
        next_attempt_at=now - timedelta(minutes=1),
    )
    await repo.save(due_run)

    # Run not yet due
    future_run = Run(
        issue_id="ISSUE-FUTURE",
        status=RunStatus.RETRY_PENDING,
        next_attempt_at=now + timedelta(hours=1),
    )
    await repo.save(future_run)

    # Run with different status
    other_run = Run(
        issue_id="ISSUE-OTHER",
        status=RunStatus.RECEIVED,
        next_attempt_at=now - timedelta(minutes=1),
    )
    await repo.save(other_run)

    due = await repo.find_due_retries(now)

    assert len(due) == 1
    assert due[0].issue_id == "ISSUE-DUE"


async def test_update_raises_when_run_not_found(async_session):
    repo = SQLAlchemyRunRepository(async_session)
    detached = Run.create(issue_id="ENG-not-saved")  # never persisted

    with pytest.raises(ValueError, match="not found for update"):
        await repo.update(detached)
