"""Integration tests for SQLAlchemyIdentityUnitOfWork rollback behaviour.

Verifies that __aexit__ calls rollback() when an exception propagates,
ensuring no partial writes survive a failed transaction.
"""

import pytest

from src.contexts.identity.adapters.persistence.unit_of_work import (
    SQLAlchemyIdentityUnitOfWork,
)
from src.contexts.identity.domain.user.email import Email
from src.contexts.identity.domain.user.entity import User


async def test_uow_rollback_on_exception_prevents_persistence(async_session) -> None:
    """Changes staged inside a failing async-with block must not persist."""
    uow = SQLAlchemyIdentityUnitOfWork(async_session)

    with pytest.raises(RuntimeError, match="simulate failure"):
        async with uow:
            user = User.create(email=Email("rollback@example.com"), name="Rollback User")
            await uow.users.save(user)
            raise RuntimeError("simulate failure")

    # Verify the save was rolled back — entity must not appear in the DB
    found = await uow.users.find_by_email(Email("rollback@example.com"))
    assert found is None


async def test_uow_rollback_does_not_commit(async_session) -> None:
    """A successful commit should persist; rollback on subsequent exception should not."""
    uow = SQLAlchemyIdentityUnitOfWork(async_session)

    # First transaction — commits successfully
    async with uow:
        await uow.users.save(
            User.create(email=Email("committed@example.com"), name="Committed User")
        )
        await uow.commit()

    # Second transaction — rolls back without commit
    with pytest.raises(ValueError, match="abort second"):
        async with uow:
            await uow.users.save(
                User.create(email=Email("aborted@example.com"), name="Aborted User")
            )
            raise ValueError("abort second")

    committed = await uow.users.find_by_email(Email("committed@example.com"))
    aborted = await uow.users.find_by_email(Email("aborted@example.com"))

    assert committed is not None
    assert aborted is None
