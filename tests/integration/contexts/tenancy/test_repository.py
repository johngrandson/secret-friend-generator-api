"""Integration tests for SQLAlchemyOrganizationRepository against SQLite."""

from uuid import uuid4

import pytest

from src.contexts.tenancy.adapters.persistence.organization.repository import (
    SQLAlchemyOrganizationRepository,
)
from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.value_objects import Slug
from src.contexts.tenancy.domain.role.value_objects import Role


def _make_org(slug: str = "acme", name: str = "Acme") -> Organization:
    return Organization.create(
        name=name, slug=Slug(slug), owner_user_id=uuid4()
    )


async def test_save_and_find_by_id(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)
    org = _make_org()

    await repo.save(org)
    found = await repo.find_by_id(org.id)

    assert found is not None
    assert found.id == org.id
    assert str(found.slug) == "acme"
    assert found.owner_count() == 1


async def test_find_by_slug(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)
    org = _make_org(slug="findme")
    await repo.save(org)

    found = await repo.find_by_slug(Slug("findme"))

    assert found is not None
    assert found.id == org.id


async def test_find_by_slug_returns_none_when_missing(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)

    result = await repo.find_by_slug(Slug("ghost"))

    assert result is None


async def test_list_for_user_returns_users_orgs_only(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)
    user = uuid4()
    other = uuid4()
    a = Organization.create(name="A", slug=Slug("a"), owner_user_id=user)
    b = Organization.create(name="B", slug=Slug("b"), owner_user_id=user)
    c = Organization.create(name="C", slug=Slug("c"), owner_user_id=other)
    for org in (a, b, c):
        await repo.save(org)

    result = await repo.list_for_user(user)

    slugs = {str(o.slug) for o in result}
    assert slugs == {"a", "b"}


async def test_list_for_user_returns_empty_when_no_memberships(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)

    result = await repo.list_for_user(uuid4())

    assert result == []


async def test_update_persists_new_name_and_added_member(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)
    org = _make_org()
    await repo.save(org)
    new_user = uuid4()

    org.name = "Renamed"
    org.add_member(new_user, Role.MEMBER)
    await repo.update(org)

    reloaded = await repo.find_by_id(org.id)
    assert reloaded is not None
    assert reloaded.name == "Renamed"
    assert reloaded.has_member(new_user)


async def test_update_persists_member_removal(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)
    org = _make_org()
    second = uuid4()
    org.add_member(second, Role.MEMBER)
    await repo.save(org)

    org.remove_member(second)
    await repo.update(org)

    reloaded = await repo.find_by_id(org.id)
    assert reloaded is not None
    assert not reloaded.has_member(second)


async def test_update_persists_role_change(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)
    org = _make_org()
    member = uuid4()
    org.add_member(member, Role.MEMBER)
    await repo.save(org)

    org.change_member_role(member, Role.ADMIN)
    await repo.update(org)

    reloaded = await repo.find_by_id(org.id)
    assert reloaded is not None
    found = reloaded.find_member(member)
    assert found is not None
    assert found.role is Role.ADMIN


async def test_update_unknown_org_raises(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)
    detached = _make_org()

    with pytest.raises(ValueError, match="not found for update"):
        await repo.update(detached)


async def test_delete_existing_returns_true(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)
    org = _make_org()
    await repo.save(org)

    deleted = await repo.delete(org.id)
    found = await repo.find_by_id(org.id)

    assert deleted is True
    assert found is None


async def test_delete_nonexistent_returns_false(async_session):
    repo = SQLAlchemyOrganizationRepository(async_session)

    result = await repo.delete(uuid4())

    assert result is False
