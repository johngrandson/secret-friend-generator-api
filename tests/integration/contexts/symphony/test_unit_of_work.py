"""Integration tests for SQLAlchemySymphonyUnitOfWork rollback behaviour.

Verifies that __aexit__ calls rollback() when an exception propagates,
ensuring no partial writes survive a failed transaction.
"""

import pytest

from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.contexts.symphony.domain.run.entity import Run


async def test_uow_rollback_on_exception_prevents_persistence(async_session) -> None:
    """Changes staged inside a failing async-with block must not persist."""
    uow = SQLAlchemySymphonyUnitOfWork(async_session)
    run = Run.create(issue_id="ENG-rollback")

    with pytest.raises(RuntimeError, match="simulate failure"):
        async with uow:
            await uow.runs.save(run)
            raise RuntimeError("simulate failure")

    # Verify the save was rolled back — entity must not appear in the DB
    found = await uow.runs.find_by_id(run.id)
    assert found is None


async def test_uow_rollback_does_not_commit(async_session) -> None:
    """A successful commit should persist; rollback on subsequent exception should not."""
    uow = SQLAlchemySymphonyUnitOfWork(async_session)
    committed_run = Run.create(issue_id="ENG-committed")

    # First transaction — commits successfully
    async with uow:
        await uow.runs.save(committed_run)
        await uow.commit()

    aborted_run = Run.create(issue_id="ENG-aborted")

    # Second transaction — rolls back without commit
    with pytest.raises(ValueError, match="abort second"):
        async with uow:
            await uow.runs.save(aborted_run)
            raise ValueError("abort second")

    committed = await uow.runs.find_by_id(committed_run.id)
    aborted = await uow.runs.find_by_id(aborted_run.id)

    assert committed is not None
    assert aborted is None
