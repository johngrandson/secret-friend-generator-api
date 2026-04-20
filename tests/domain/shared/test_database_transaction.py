import pytest
from sqlalchemy.orm import Session

from src.domain.shared.database_transaction import transaction
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
