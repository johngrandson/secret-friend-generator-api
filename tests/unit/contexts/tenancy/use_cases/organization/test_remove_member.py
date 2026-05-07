"""Unit tests for RemoveMemberUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.events import MemberRemoved
from src.contexts.tenancy.domain.organization.value_objects import Slug
from src.contexts.tenancy.domain.role.value_objects import Role
from src.contexts.tenancy.use_cases.organization.remove_member import (
    RemoveMemberRequest,
    RemoveMemberUseCase,
)
from tests.conftest import FakeTenancyUoW


@pytest.fixture
def uow() -> FakeTenancyUoW:
    return FakeTenancyUoW()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def use_case(uow, publisher):
    return RemoveMemberUseCase(uow=uow, event_publisher=publisher)


async def test_remove_member_success(use_case, uow, publisher):
    owner = uuid4()
    org = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=owner)
    other = uuid4()
    org.add_member(other, Role.MEMBER)
    org.pull_events()
    uow.organizations.find_by_id.return_value = org
    uow.organizations.update.return_value = org

    resp = await use_case.execute(
        RemoveMemberRequest(organization_id=org.id, user_id=other)
    )

    assert resp.success is True
    assert uow.committed is True
    events = publisher.publish.call_args[0][0]
    assert any(
        isinstance(e, MemberRemoved) and e.user_id == other for e in events
    )


async def test_remove_last_owner_blocked(use_case, uow, publisher):
    owner = uuid4()
    org = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=owner)
    org.pull_events()
    uow.organizations.find_by_id.return_value = org

    resp = await use_case.execute(
        RemoveMemberRequest(organization_id=org.id, user_id=owner)
    )

    assert resp.success is False
    assert "last OWNER" in (resp.error_message or "")
    uow.organizations.update.assert_not_called()
    publisher.publish.assert_not_called()


async def test_remove_member_organization_not_found(use_case, uow, publisher):
    uow.organizations.find_by_id.return_value = None

    resp = await use_case.execute(
        RemoveMemberRequest(organization_id=uuid4(), user_id=uuid4())
    )

    assert resp.success is False
    assert resp.error_message == "Organization not found."
