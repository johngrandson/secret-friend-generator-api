"""Unit tests for ChangeMemberRoleUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.events import MemberRoleChanged
from src.contexts.tenancy.domain.organization.value_objects import Slug
from src.contexts.tenancy.domain.role.value_objects import Role
from src.contexts.tenancy.use_cases.organization.change_role import (
    ChangeMemberRoleRequest,
    ChangeMemberRoleUseCase,
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
    return ChangeMemberRoleUseCase(uow=uow, event_publisher=publisher)


async def test_change_role_success(use_case, uow, publisher):
    org = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=uuid4())
    member = uuid4()
    org.add_member(member, Role.MEMBER)
    org.pull_events()
    uow.organizations.find_by_id.return_value = org
    uow.organizations.update.return_value = org

    resp = await use_case.execute(
        ChangeMemberRoleRequest(
            organization_id=org.id, user_id=member, new_role=Role.ADMIN
        )
    )

    assert resp.success is True
    events = publisher.publish.call_args[0][0]
    evt = next((e for e in events if isinstance(e, MemberRoleChanged)), None)
    assert evt is not None
    assert evt.new_role is Role.ADMIN


async def test_demote_last_owner_blocked(use_case, uow, publisher):
    owner = uuid4()
    org = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=owner)
    org.pull_events()
    uow.organizations.find_by_id.return_value = org

    resp = await use_case.execute(
        ChangeMemberRoleRequest(
            organization_id=org.id, user_id=owner, new_role=Role.MEMBER
        )
    )

    assert resp.success is False
    assert "last OWNER" in (resp.error_message or "")
    uow.organizations.update.assert_not_called()


async def test_change_role_organization_not_found(use_case, uow, publisher):
    uow.organizations.find_by_id.return_value = None

    resp = await use_case.execute(
        ChangeMemberRoleRequest(
            organization_id=uuid4(), user_id=uuid4(), new_role=Role.ADMIN
        )
    )

    assert resp.success is False
    assert resp.error_message == "Organization not found."
