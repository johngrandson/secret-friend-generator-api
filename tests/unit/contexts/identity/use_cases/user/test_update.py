"""Unit tests for UpdateUserUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.identity.domain.user.email import Email
from src.contexts.identity.domain.user.entity import User
from src.contexts.identity.use_cases.user.dto import UserDTO
from src.contexts.identity.use_cases.user.update import UpdateUserRequest, UpdateUserUseCase
from tests.conftest import FakeIdentityUoW


@pytest.fixture
def uow() -> FakeIdentityUoW:
    return FakeIdentityUoW()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def use_case(uow, publisher):
    return UpdateUserUseCase(uow=uow, event_publisher=publisher)


async def test_update_name_success(use_case, uow, publisher):
    user = User.create(email=Email("a@b.com"), name="Old Name")
    uow.users.find_by_id.return_value = user
    uow.users.update.return_value = user

    resp = await use_case.execute(UpdateUserRequest(user_id=user.id, name="New Name"))

    assert resp.success is True
    assert isinstance(resp.user, UserDTO)
    assert resp.user.name == "New Name"
    assert uow.committed is True


async def test_update_is_active_false(use_case, uow, publisher):
    user = User.create(email=Email("a@b.com"), name="Alice")
    uow.users.find_by_id.return_value = user
    uow.users.update.return_value = user

    resp = await use_case.execute(UpdateUserRequest(user_id=user.id, is_active=False))

    assert resp.success is True
    assert resp.user.is_active is False


async def test_update_nonexistent_user(use_case, uow, publisher):
    uow.users.find_by_id.return_value = None

    resp = await use_case.execute(UpdateUserRequest(user_id=uuid4(), name="X"))

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    uow.users.update.assert_not_called()


async def test_update_blank_name_fails(use_case, uow, publisher):
    user = User.create(email=Email("a@b.com"), name="Alice")
    uow.users.find_by_id.return_value = user

    resp = await use_case.execute(UpdateUserRequest(user_id=user.id, name="  "))

    assert resp.success is False
    uow.users.update.assert_not_called()


async def test_update_is_active_true_activates_user(use_case, uow, publisher):
    user = User.create(email=Email("a@b.com"), name="Alice")
    user.deactivate()  # start deactivated so activate() has effect
    uow.users.find_by_id.return_value = user
    uow.users.update.return_value = user

    resp = await use_case.execute(UpdateUserRequest(user_id=user.id, is_active=True))

    assert resp.success is True
    assert resp.user.is_active is True
    assert uow.committed is True
