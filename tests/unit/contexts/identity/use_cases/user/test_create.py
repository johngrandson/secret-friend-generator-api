"""Unit tests for CreateUserUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.contexts.identity.domain.user.email import Email
from src.contexts.identity.domain.user.entity import User
from src.contexts.identity.use_cases.user.create import CreateUserRequest, CreateUserUseCase
from src.contexts.identity.use_cases.user.dto import UserDTO
from tests.conftest import FakeIdentityUoW


@pytest.fixture
def uow() -> FakeIdentityUoW:
    return FakeIdentityUoW()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def use_case(uow, publisher):
    return CreateUserUseCase(uow=uow, event_publisher=publisher)


async def test_create_user_success(use_case, uow, publisher):
    uow.users.find_by_email.return_value = None
    saved_user = User.create(email=Email("new@example.com"), name="Alice")
    uow.users.save.return_value = saved_user

    resp = await use_case.execute(
        CreateUserRequest(email="new@example.com", name="Alice")
    )

    assert resp.success is True
    assert isinstance(resp.user, UserDTO)
    assert resp.user.email == "new@example.com"
    assert resp.error_message is None
    assert uow.committed is True
    publisher.publish.assert_called_once()


async def test_create_user_publisher_receives_user_created_event(
    use_case, uow, publisher
):
    uow.users.find_by_email.return_value = None
    saved_user = User.create(email=Email("evt@example.com"), name="Bob")
    uow.users.save.return_value = saved_user

    await use_case.execute(CreateUserRequest(email="evt@example.com", name="Bob"))

    events = publisher.publish.call_args[0][0]
    from src.contexts.identity.domain.user.events import UserCreated

    assert len(events) == 1
    assert isinstance(events[0], UserCreated)
    assert events[0].email == "evt@example.com"


async def test_create_user_duplicate_email(use_case, uow, publisher):
    uow.users.find_by_email.return_value = User.create(
        email=Email("dup@example.com"), name="Existing"
    )

    resp = await use_case.execute(
        CreateUserRequest(email="dup@example.com", name="New")
    )

    assert resp.success is False
    assert "already registered" in resp.error_message
    uow.users.save.assert_not_called()
    publisher.publish.assert_not_called()


async def test_create_user_invalid_email(use_case, uow, publisher):
    resp = await use_case.execute(CreateUserRequest(email="not-valid", name="Alice"))

    assert resp.success is False
    assert resp.error_message is not None
    uow.users.find_by_email.assert_not_called()
    publisher.publish.assert_not_called()


async def test_create_user_blank_name(use_case, uow, publisher):
    uow.users.find_by_email.return_value = None

    resp = await use_case.execute(CreateUserRequest(email="ok@example.com", name="  "))

    assert resp.success is False
    assert resp.error_message is not None
    publisher.publish.assert_not_called()
