"""Unit tests for ListUsersUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.domain.user.email import Email
from src.domain.user.entity import User
from src.use_cases.user.dto import UserDTO
from src.use_cases.user.list import ListUsersRequest, ListUsersUseCase


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def use_case(repo):
    return ListUsersUseCase(user_repository=repo)


async def test_list_returns_all_users(use_case, repo):
    users = [
        User.create(email=Email("a@b.com"), name="Alice"),
        User.create(email=Email("c@d.com"), name="Bob"),
    ]
    repo.list.return_value = users

    resp = await use_case.execute(ListUsersRequest())

    assert resp.success is True
    assert len(resp.users) == 2
    assert all(isinstance(u, UserDTO) for u in resp.users)
    assert resp.users[0].name == "Alice"
    assert resp.users[1].name == "Bob"
    repo.list.assert_called_once_with(limit=20, offset=0)


async def test_list_passes_pagination(use_case, repo):
    repo.list.return_value = []

    await use_case.execute(ListUsersRequest(limit=5, offset=10))

    repo.list.assert_called_once_with(limit=5, offset=10)


async def test_list_empty_returns_empty_list(use_case, repo):
    repo.list.return_value = []

    resp = await use_case.execute(ListUsersRequest())

    assert resp.users == []
