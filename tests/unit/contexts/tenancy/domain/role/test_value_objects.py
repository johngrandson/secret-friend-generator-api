"""Unit tests for the Role enum value object."""

import pytest

from src.contexts.tenancy.domain.role.value_objects import Role


def test_role_values():
    assert Role.OWNER.value == "OWNER"
    assert Role.ADMIN.value == "ADMIN"
    assert Role.MEMBER.value == "MEMBER"


@pytest.mark.parametrize(
    "role,expected",
    [(Role.OWNER, True), (Role.ADMIN, True), (Role.MEMBER, False)],
)
def test_can_manage_members(role, expected):
    assert role.can_manage_members() is expected


def test_only_owner_can_grant_owner():
    assert Role.OWNER.can_change_role_to(Role.OWNER) is True
    assert Role.ADMIN.can_change_role_to(Role.OWNER) is False
    assert Role.MEMBER.can_change_role_to(Role.OWNER) is False


def test_admin_can_change_non_owner_roles():
    assert Role.ADMIN.can_change_role_to(Role.ADMIN) is True
    assert Role.ADMIN.can_change_role_to(Role.MEMBER) is True


def test_member_cannot_change_roles():
    assert Role.MEMBER.can_change_role_to(Role.MEMBER) is False
    assert Role.MEMBER.can_change_role_to(Role.ADMIN) is False
