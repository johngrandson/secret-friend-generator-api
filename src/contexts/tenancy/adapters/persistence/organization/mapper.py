"""Mapping functions between Organization aggregate and ORM rows."""

from collections.abc import Iterable

from src.contexts.tenancy.adapters.persistence.organization.model import (
    OrganizationMemberModel,
    OrganizationModel,
)
from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.value_objects import (
    Membership,
    Slug,
)
from src.contexts.tenancy.domain.role.value_objects import Role


def to_entity(
    org_row: OrganizationModel,
    member_rows: Iterable[OrganizationMemberModel],
) -> Organization:
    """Rehydrate an Organization aggregate from its ORM rows."""
    return Organization(
        id=org_row.id,
        name=org_row.name,
        slug=Slug(org_row.slug),
        members={
            Membership(user_id=row.user_id, role=Role(row.role))
            for row in member_rows
        },
        created_at=org_row.created_at,
    )


def to_org_model(organization: Organization) -> OrganizationModel:
    """Convert the aggregate root header to an OrganizationModel row."""
    return OrganizationModel(
        id=organization.id,
        name=organization.name,
        slug=str(organization.slug),
        created_at=organization.created_at,
    )


def to_member_models(
    organization: Organization,
) -> list[OrganizationMemberModel]:
    """Convert the aggregate's membership set to ORM rows."""
    return [
        OrganizationMemberModel(
            organization_id=organization.id,
            user_id=m.user_id,
            role=m.role.value,
        )
        for m in organization.members
    ]
