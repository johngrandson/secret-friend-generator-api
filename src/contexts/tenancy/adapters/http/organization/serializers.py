"""Serialization helpers — OrganizationDTO → JSON-serialisable dict."""

from src.contexts.tenancy.use_cases.organization.dto import (
    MembershipDTO,
    OrganizationDTO,
)


def to_membership_output(dto: MembershipDTO) -> dict:
    return {
        "user_id": str(dto.user_id),
        "role": dto.role.value,
    }


def to_organization_output(dto: OrganizationDTO) -> dict:
    return {
        "id": str(dto.id),
        "name": dto.name,
        "slug": dto.slug,
        "members": [to_membership_output(m) for m in dto.members],
        "created_at": dto.created_at.isoformat(),
    }
