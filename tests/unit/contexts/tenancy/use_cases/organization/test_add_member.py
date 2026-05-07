"""Unit tests for AddMemberUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.events import MemberAdded
from src.contexts.tenancy.domain.organization.value_objects import Slug
from src.contexts.tenancy.domain.role.value_objects import Role
from src.contexts.tenancy.use_cases.organization.add_member import (
    AddMemberRequest,
    AddMemberUseCase,
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
    return AddMemberUseCase(uow=uow, event_publisher=publisher)


async def test_add_member_success(use_case, uow, publisher):
    org = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=uuid4())
    org.pull_events()
    uow.organizations.find_by_id.return_value = org
    uow.organizations.update.return_value = org

    new_user = uuid4()
    resp = await use_case.execute(
        AddMemberRequest(
            organization_id=org.id, user_id=new_user, role=Role.MEMBER
        )
    )

    assert resp.success is True
    assert uow.committed is True
    publisher.publish.assert_called_once()
    events = publisher.publish.call_args[0][0]
    assert any(
        isinstance(e, MemberAdded) and e.user_id == new_user for e in events
    )


async def test_add_member_organization_not_found(use_case, uow, publisher):
    uow.organizations.find_by_id.return_value = None

    resp = await use_case.execute(
        AddMemberRequest(
            organization_id=uuid4(), user_id=uuid4(), role=Role.MEMBER
        )
    )

    assert resp.success is False
    assert resp.error_message == "Organization not found."
    uow.organizations.update.assert_not_called()
    publisher.publish.assert_not_called()


async def test_add_member_already_member(use_case, uow, publisher):
    owner = uuid4()
    org = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=owner)
    org.pull_events()
    uow.organizations.find_by_id.return_value = org

    resp = await use_case.execute(
        AddMemberRequest(organization_id=org.id, user_id=owner, role=Role.ADMIN)
    )

    assert resp.success is False
    assert "already a member" in (resp.error_message or "")
    uow.organizations.update.assert_not_called()
    publisher.publish.assert_not_called()
