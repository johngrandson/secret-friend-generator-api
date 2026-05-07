"""Unit tests for the Organization aggregate."""

from uuid import UUID, uuid4

import pytest

from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.events import (
    MemberAdded,
    MemberRemoved,
    MemberRoleChanged,
    OrganizationCreated,
)
from src.contexts.tenancy.domain.organization.value_objects import Slug
from src.contexts.tenancy.domain.role.value_objects import Role


def _make_org(name: str = "Acme") -> tuple[Organization, UUID]:
    owner_id = uuid4()
    org = Organization.create(name=name, slug=Slug("acme"), owner_user_id=owner_id)
    org.pull_events()
    return org, owner_id


# ---------------- create ----------------


def test_create_seeds_owner_membership():
    owner_id = uuid4()
    org = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=owner_id)
    assert org.owner_count() == 1
    assert org.has_member(owner_id)
    member = org.find_member(owner_id)
    assert member is not None
    assert member.role is Role.OWNER


def test_create_collects_organization_created_event():
    owner_id = uuid4()
    org = Organization.create(name="Acme", slug=Slug("acme"), owner_user_id=owner_id)
    events = org.pull_events()
    assert len(events) == 1
    evt = events[0]
    assert isinstance(evt, OrganizationCreated)
    assert evt.organization_id == org.id
    assert evt.name == "Acme"
    assert evt.slug == "acme"
    assert evt.owner_user_id == owner_id


def test_create_blank_name_raises():
    with pytest.raises(ValueError, match="must not be blank"):
        Organization.create(name="   ", slug=Slug("acme"), owner_user_id=uuid4())


# ---------------- add_member ----------------


def test_add_member_appends_membership_and_emits_event():
    org, _ = _make_org()
    new_user = uuid4()
    org.add_member(new_user, Role.MEMBER)
    assert org.has_member(new_user)
    events = org.pull_events()
    assert len(events) == 1
    evt = events[0]
    assert isinstance(evt, MemberAdded)
    assert evt.user_id == new_user
    assert evt.role is Role.MEMBER


def test_add_member_duplicate_raises():
    org, owner_id = _make_org()
    with pytest.raises(ValueError, match="already a member"):
        org.add_member(owner_id, Role.ADMIN)


# ---------------- remove_member ----------------


def test_remove_member_drops_membership_and_emits_event():
    org, _ = _make_org()
    new_user = uuid4()
    org.add_member(new_user, Role.MEMBER)
    org.pull_events()

    org.remove_member(new_user)
    assert not org.has_member(new_user)
    events = org.pull_events()
    assert len(events) == 1
    evt = events[0]
    assert isinstance(evt, MemberRemoved)
    assert evt.user_id == new_user


def test_remove_member_not_a_member_raises():
    org, _ = _make_org()
    with pytest.raises(ValueError, match="not a member"):
        org.remove_member(uuid4())


def test_remove_last_owner_raises():
    org, owner_id = _make_org()
    with pytest.raises(ValueError, match="last OWNER"):
        org.remove_member(owner_id)


def test_remove_owner_when_other_owners_exist_succeeds():
    org, owner_id = _make_org()
    second_owner = uuid4()
    org.add_member(second_owner, Role.OWNER)
    org.pull_events()

    org.remove_member(owner_id)
    assert org.owner_count() == 1
    assert not org.has_member(owner_id)


# ---------------- change_member_role ----------------


def test_change_member_role_emits_event():
    org, _ = _make_org()
    member = uuid4()
    org.add_member(member, Role.MEMBER)
    org.pull_events()

    org.change_member_role(member, Role.ADMIN)
    events = org.pull_events()
    assert len(events) == 1
    evt = events[0]
    assert isinstance(evt, MemberRoleChanged)
    assert evt.user_id == member
    assert evt.old_role is Role.MEMBER
    assert evt.new_role is Role.ADMIN


def test_change_member_role_no_op_emits_no_event():
    org, _ = _make_org()
    member = uuid4()
    org.add_member(member, Role.MEMBER)
    org.pull_events()

    org.change_member_role(member, Role.MEMBER)
    assert org.pull_events() == []


def test_change_member_role_not_a_member_raises():
    org, _ = _make_org()
    with pytest.raises(ValueError, match="not a member"):
        org.change_member_role(uuid4(), Role.ADMIN)


def test_demote_last_owner_raises():
    org, owner_id = _make_org()
    with pytest.raises(ValueError, match="last OWNER"):
        org.change_member_role(owner_id, Role.MEMBER)


def test_demote_owner_when_other_owners_exist_succeeds():
    org, owner_id = _make_org()
    second_owner = uuid4()
    org.add_member(second_owner, Role.OWNER)
    org.pull_events()

    org.change_member_role(owner_id, Role.MEMBER)
    assert org.owner_count() == 1
    member = org.find_member(owner_id)
    assert member is not None
    assert member.role is Role.MEMBER


def test_promote_member_to_owner():
    org, _ = _make_org()
    member = uuid4()
    org.add_member(member, Role.MEMBER)
    org.pull_events()

    org.change_member_role(member, Role.OWNER)
    assert org.owner_count() == 2
