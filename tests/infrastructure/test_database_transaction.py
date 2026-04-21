import pytest
from sqlalchemy.orm import Session

from src.infrastructure.persistence import transaction
from src.domain.group.model import Group
from src.domain.group.schemas import GroupCreate
from src.domain.group.repository import GroupRepository


def test_transaction_commits_on_success(db_session: Session):
    """Context manager commits when no exception is raised."""
    with transaction(db_session):
        group = GroupRepository.create(
            GroupCreate(name="Commit Test", description="desc"), db_session
        )

    fetched = db_session.get(Group, group.id)
    assert fetched is not None
    assert fetched.name == "Commit Test"


def test_transaction_rollbacks_on_exception(db_session: Session):
    """Context manager rolls back and re-raises on exception."""
    group_id = None
    with pytest.raises(RuntimeError, match="intentional"):
        with transaction(db_session):
            group = GroupRepository.create(
                GroupCreate(name="Rollback Test", description="desc"), db_session
            )
            group_id = group.id
            raise RuntimeError("intentional error")

    # After rollback the object should no longer be present
    fetched = db_session.get(Group, group_id)
    assert fetched is None


def test_transaction_reraises_original_exception(db_session: Session):
    """The original exception type is preserved after rollback."""

    class CustomError(Exception):
        pass

    with pytest.raises(CustomError):
        with transaction(db_session):
            raise CustomError("boom")


def test_transaction_yields_db_session(db_session: Session):
    """The context variable yielded is the same session object."""
    with transaction(db_session) as sess:
        assert sess is db_session


def test_transaction_is_reentrant_inner_yields_same_session(db_session: Session):
    """Nested transaction() calls yield the same session object."""
    with transaction(db_session) as outer:
        with transaction(db_session) as inner:
            assert inner is outer
            assert inner is db_session


def test_transaction_is_reentrant_inner_does_not_commit(db_session: Session):
    """Inner transaction() exits without committing — outer owns the commit.

    Both records created inside nested transactions must survive after the
    outermost block closes, proving the outer commit covered both writes.
    """
    with transaction(db_session) as outer:
        group_outer = GroupRepository.create(
            GroupCreate(name="Outer", description="outer"), outer
        )

        with transaction(db_session) as inner:
            # _in_transaction flag is already set — inner must not commit
            assert db_session.info.get("_in_transaction") is True
            group_inner = GroupRepository.create(
                GroupCreate(name="Inner", description="inner"), inner
            )

    # Outer commit ran — both rows must be visible
    assert db_session.get(Group, group_outer.id) is not None
    assert db_session.get(Group, group_inner.id) is not None


def test_transaction_flag_cleared_after_outer_exits(db_session: Session):
    """_in_transaction flag is removed from session.info once outer block ends."""
    with transaction(db_session):
        with transaction(db_session):
            pass

    assert "_in_transaction" not in db_session.info


def test_transaction_flag_cleared_after_outer_exception(db_session: Session):
    """_in_transaction flag is removed even when outer block raises."""
    with pytest.raises(RuntimeError):
        with transaction(db_session):
            raise RuntimeError("boom")

    assert "_in_transaction" not in db_session.info
