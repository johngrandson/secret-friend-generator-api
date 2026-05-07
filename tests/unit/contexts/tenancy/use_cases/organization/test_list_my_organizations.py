"""Unit tests for ListMyOrganizationsUseCase."""

from uuid import uuid4

import pytest

from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.value_objects import Slug
from src.contexts.tenancy.use_cases.organization.list_my_organizations import (
    ListMyOrganizationsRequest,
    ListMyOrganizationsUseCase,
)
from tests.conftest import FakeTenancyUoW


@pytest.fixture
def uow() -> FakeTenancyUoW:
    return FakeTenancyUoW()


@pytest.fixture
def use_case(uow):
    return ListMyOrganizationsUseCase(uow=uow)


async def test_list_returns_dtos_for_user_orgs(use_case, uow):
    user_id = uuid4()
    a = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=user_id)
    b = Organization.create(name="Beta", slug=Slug("beta"), owner_user_id=user_id)
    uow.organizations.list_for_user.return_value = [a, b]

    resp = await use_case.execute(ListMyOrganizationsRequest(user_id=user_id))

    assert len(resp.organizations) == 2
    slugs = {o.slug for o in resp.organizations}
    assert slugs == {"acme", "beta"}


async def test_list_returns_empty_tuple_when_user_has_no_orgs(use_case, uow):
    uow.organizations.list_for_user.return_value = []

    resp = await use_case.execute(ListMyOrganizationsRequest(user_id=uuid4()))

    assert resp.organizations == ()
