"""Unit tests for GetUserUseCase."""

from uuid import uuid4

import pytest

from src.contexts.identity.domain.user.email import Email
from src.contexts.identity.domain.user.entity import User
from src.contexts.identity.use_cases.user.dto import UserDTO
from src.contexts.identity.use_cases.user.get import GetUserRequest, GetUserUseCase
from tests.conftest import FakeIdentityUoW


@pytest.fixture
def uow() -> FakeIdentityUoW:
    return FakeIdentityUoW()


@pytest.fixture
def use_case(uow):
    return GetUserUseCase(uow=uow)


async def test_get_existing_user(use_case, uow):
    user = User.create(email=Email("a@b.com"), name="Alice")
    uow.users.find_by_id.return_value = user

    resp = await use_case.execute(GetUserRequest(user_id=user.id))

    assert resp.success is True
    assert isinstance(resp.user, UserDTO)
    assert resp.user.id == user.id
    assert resp.user.email == "a@b.com"


async def test_get_nonexistent_user(use_case, uow):
    uow.users.find_by_id.return_value = None

    resp = await use_case.execute(GetUserRequest(user_id=uuid4()))

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    assert resp.user is None
