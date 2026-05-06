"""Unit tests for DeleteUserUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.use_cases.user.delete import DeleteUserRequest, DeleteUserUseCase


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def use_case(repo, publisher):
    return DeleteUserUseCase(user_repository=repo, event_publisher=publisher)


async def test_delete_existing_user(use_case, repo, publisher):
    repo.delete.return_value = True
    user_id = uuid4()

    resp = await use_case.execute(DeleteUserRequest(user_id=user_id))

    assert resp.success is True
    repo.delete.assert_called_once_with(user_id)
    publisher.publish.assert_called_once()


async def test_delete_publishes_user_deleted_event(use_case, repo, publisher):
    repo.delete.return_value = True
    user_id = uuid4()

    await use_case.execute(DeleteUserRequest(user_id=user_id))

    from src.domain.user.events import UserDeleted
    events = publisher.publish.call_args[0][0]
    assert len(events) == 1
    assert isinstance(events[0], UserDeleted)
    assert events[0].user_id == user_id


async def test_delete_nonexistent_user(use_case, repo, publisher):
    repo.delete.return_value = False

    resp = await use_case.execute(DeleteUserRequest(user_id=uuid4()))

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    publisher.publish.assert_not_called()
