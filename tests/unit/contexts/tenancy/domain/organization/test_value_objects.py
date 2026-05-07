"""Unit tests for Slug and Membership value objects."""

from uuid import uuid4

import pytest

from src.contexts.tenancy.domain.organization.value_objects import (
    Membership,
    Slug,
)
from src.contexts.tenancy.domain.role.value_objects import Role


@pytest.mark.parametrize(
    "value",
    ["acme", "acme-co", "a", "acme-2026", "x" * 64, "ab-cd-ef-12"],
)
def test_slug_accepts_valid_values(value):
    assert str(Slug(value)) == value


@pytest.mark.parametrize(
    "value",
    ["", "Acme", "ACME", "-acme", "acme-", "acme co", "acme/co", "x" * 65, "_acme"],
)
def test_slug_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        Slug(value)


def test_slug_is_immutable():
    slug = Slug("acme")
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        slug.value = "other"  # type: ignore[misc]


def test_membership_equality_by_value():
    user_id = uuid4()
    a = Membership(user_id=user_id, role=Role.OWNER)
    b = Membership(user_id=user_id, role=Role.OWNER)
    assert a == b
    assert hash(a) == hash(b)


def test_membership_different_role_not_equal():
    user_id = uuid4()
    a = Membership(user_id=user_id, role=Role.OWNER)
    b = Membership(user_id=user_id, role=Role.MEMBER)
    assert a != b
