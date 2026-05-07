"""Unit tests for CreateOrganizationUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.events import OrganizationCreated
from src.contexts.tenancy.domain.organization.value_objects import Slug
from src.contexts.tenancy.use_cases.organization.create import (
    CreateOrganizationRequest,
    CreateOrganizationUseCase,
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
    return CreateOrganizationUseCase(uow=uow, event_publisher=publisher)


async def test_create_success(use_case, uow, publisher):
    uow.organizations.find_by_slug.return_value = None
    owner = uuid4()
    saved = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=owner)
    uow.organizations.save.return_value = saved

    resp = await use_case.execute(
        CreateOrganizationRequest(name="Acme", slug="acme", owner_user_id=owner)
    )

    assert resp.success is True
    assert resp.organization is not None
    assert resp.organization.name == "Acme"
    assert resp.organization.slug == "acme"
    assert uow.committed is True
    publisher.publish.assert_called_once()


async def test_create_publishes_organization_created_event(
    use_case, uow, publisher
):
    uow.organizations.find_by_slug.return_value = None
    owner = uuid4()
    saved = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=owner)
    uow.organizations.save.return_value = saved

    await use_case.execute(
        CreateOrganizationRequest(name="Acme", slug="acme", owner_user_id=owner)
    )

    events = publisher.publish.call_args[0][0]
    assert len(events) == 1
    assert isinstance(events[0], OrganizationCreated)
    assert events[0].owner_user_id == owner


async def test_create_invalid_slug(use_case, uow, publisher):
    resp = await use_case.execute(
        CreateOrganizationRequest(
            name="Acme", slug="Invalid Slug!", owner_user_id=uuid4()
        )
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.organizations.find_by_slug.assert_not_called()
    publisher.publish.assert_not_called()


async def test_create_duplicate_slug(use_case, uow, publisher):
    existing = Organization.create(
        name="Existing", slug=Slug("acme"), owner_user_id=uuid4()
    )
    uow.organizations.find_by_slug.return_value = existing

    resp = await use_case.execute(
        CreateOrganizationRequest(name="Acme", slug="acme", owner_user_id=uuid4())
    )

    assert resp.success is False
    assert "already taken" in (resp.error_message or "").lower()
    uow.organizations.save.assert_not_called()
    publisher.publish.assert_not_called()


async def test_create_blank_name(use_case, uow, publisher):
    uow.organizations.find_by_slug.return_value = None

    resp = await use_case.execute(
        CreateOrganizationRequest(name="   ", slug="acme", owner_user_id=uuid4())
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.organizations.save.assert_not_called()
    publisher.publish.assert_not_called()
