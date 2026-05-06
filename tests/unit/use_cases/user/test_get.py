"""Unit tests for GetUserUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.user.email import Email
from src.domain.user.entity import User
from src.use_cases.user.dto import UserDTO
from src.use_cases.user.get import GetUserRequest, GetUserUseCase


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def use_case(repo):
    return GetUserUseCase(user_repository=repo)


async def test_get_existing_user(use_case, repo):
    user = User.create(email=Email("a@b.com"), name="Alice")
    repo.find_by_id.return_value = user

    resp = await use_case.execute(GetUserRequest(user_id=user.id))

    assert resp.success is True
    assert isinstance(resp.user, UserDTO)
    assert resp.user.id == user.id
    assert resp.user.email == "a@b.com"


async def test_get_nonexistent_user(use_case, repo):
    repo.find_by_id.return_value = None

    resp = await use_case.execute(GetUserRequest(user_id=uuid4()))

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    assert resp.user is None
