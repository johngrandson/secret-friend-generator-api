"""DTOs for Organization use-case responses."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.value_objects import Membership
from src.contexts.tenancy.domain.role.value_objects import Role


@dataclass(frozen=True)
class MembershipDTO:
    user_id: UUID
    role: Role

    @classmethod
    def from_value_object(cls, membership: Membership) -> "MembershipDTO":
        return cls(user_id=membership.user_id, role=membership.role)


@dataclass(frozen=True)
class OrganizationDTO:
    id: UUID
    name: str
    slug: str
    members: tuple[MembershipDTO, ...]
    created_at: datetime

    @classmethod
    def from_entity(cls, organization: Organization) -> "OrganizationDTO":
        return cls(
            id=organization.id,
            name=organization.name,
            slug=str(organization.slug),
            members=tuple(
                MembershipDTO.from_value_object(m) for m in organization.members
            ),
            created_at=organization.created_at,
        )
