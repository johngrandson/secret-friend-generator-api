"""Unit tests for UpdateUserUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.user.email import Email
from src.domain.user.entity import User
from src.use_cases.user.dto import UserDTO
from src.use_cases.user.update import UpdateUserRequest, UpdateUserUseCase


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def use_case(repo, publisher):
    return UpdateUserUseCase(user_repository=repo, event_publisher=publisher)


async def test_update_name_success(use_case, repo, publisher):
    user = User.create(email=Email("a@b.com"), name="Old Name")
    repo.find_by_id.return_value = user
    repo.update.return_value = user

    resp = await use_case.execute(UpdateUserRequest(user_id=user.id, name="New Name"))

    assert resp.success is True
    assert isinstance(resp.user, UserDTO)
    assert resp.user.name == "New Name"


async def test_update_is_active_false(use_case, repo, publisher):
    user = User.create(email=Email("a@b.com"), name="Alice")
    repo.find_by_id.return_value = user
    repo.update.return_value = user

    resp = await use_case.execute(UpdateUserRequest(user_id=user.id, is_active=False))

    assert resp.success is True
    assert resp.user.is_active is False


async def test_update_nonexistent_user(use_case, repo, publisher):
    repo.find_by_id.return_value = None

    resp = await use_case.execute(UpdateUserRequest(user_id=uuid4(), name="X"))

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    repo.update.assert_not_called()


async def test_update_blank_name_fails(use_case, repo, publisher):
    user = User.create(email=Email("a@b.com"), name="Alice")
    repo.find_by_id.return_value = user

    resp = await use_case.execute(UpdateUserRequest(user_id=user.id, name="  "))

    assert resp.success is False
    repo.update.assert_not_called()
