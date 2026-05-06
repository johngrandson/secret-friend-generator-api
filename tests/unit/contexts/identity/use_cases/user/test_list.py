"""Unit tests for ListUsersUseCase."""

import pytest

from src.contexts.identity.domain.user.email import Email
from src.contexts.identity.domain.user.entity import User
from src.contexts.identity.use_cases.user.dto import UserDTO
from src.contexts.identity.use_cases.user.list import ListUsersRequest, ListUsersUseCase
from tests.conftest import FakeIdentityUoW


@pytest.fixture
def uow() -> FakeIdentityUoW:
    return FakeIdentityUoW()


@pytest.fixture
def use_case(uow):
    return ListUsersUseCase(uow=uow)


async def test_list_returns_all_users(use_case, uow):
    users = [
        User.create(email=Email("a@b.com"), name="Alice"),
        User.create(email=Email("c@d.com"), name="Bob"),
    ]
    uow.users.list.return_value = users

    resp = await use_case.execute(ListUsersRequest())

    assert resp.success is True
    assert len(resp.users) == 2
    assert all(isinstance(u, UserDTO) for u in resp.users)
    assert resp.users[0].name == "Alice"
    assert resp.users[1].name == "Bob"
    uow.users.list.assert_called_once_with(limit=20, offset=0)


async def test_list_passes_pagination(use_case, uow):
    uow.users.list.return_value = []

    await use_case.execute(ListUsersRequest(limit=5, offset=10))

    uow.users.list.assert_called_once_with(limit=5, offset=10)


async def test_list_empty_returns_empty_list(use_case, uow):
    uow.users.list.return_value = []

    resp = await use_case.execute(ListUsersRequest())

    assert resp.users == []
