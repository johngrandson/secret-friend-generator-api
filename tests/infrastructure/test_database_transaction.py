import pytest
from sqlalchemy.orm import Session

from src.domain.group.entities import Group
from src.infrastructure.persistence import transaction
from src.infrastructure.persistence.models import GroupORM
from src.infrastructure.repositories.group_repository import (
    PostgresGroupRepository,
)


def _make_group(name: str = "Test", description: str = "desc") -> Group:
    return Group(name=name, description=description)


def test_transaction_commits_on_success(db_session: Session):
    """Context manager commits when no exception is raised."""
    repo = PostgresGroupRepository(db_session)
    with transaction(db_session):
        group = repo.create(_make_group("Commit Test"))

    fetched = db_session.get(GroupORM, group.id)
    assert fetched is not None
    assert fetched.name == "Commit Test"


def test_transaction_rollbacks_on_exception(db_session: Session):
    """Context manager rolls back and re-raises on exception."""
    repo = PostgresGroupRepository(db_session)
    group_id = None
    with pytest.raises(RuntimeError, match="intentional"):
        with transaction(db_session):
            group = repo.create(_make_group("Rollback Test"))
            group_id = group.id
            raise RuntimeError("intentional error")

    fetched = db_session.get(GroupORM, group_id)
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


def test_transaction_is_reentrant_inner_yields_same_session(
    db_session: Session,
):
    """Nested transaction() calls yield the same session object."""
    with transaction(db_session) as outer:
        with transaction(db_session) as inner:
            assert inner is outer
            assert inner is db_session


def test_transaction_is_reentrant_inner_does_not_commit(db_session: Session):
    """Inner transaction() exits without committing — outer owns the commit."""
    repo = PostgresGroupRepository(db_session)
    with transaction(db_session):
        outer_group = repo.create(_make_group("Outer", "outer"))

        with transaction(db_session):
            assert db_session.info.get("_in_transaction") is True
            inner_group = repo.create(_make_group("Inner", "inner"))

    assert db_session.get(GroupORM, outer_group.id) is not None
    assert db_session.get(GroupORM, inner_group.id) is not None


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
