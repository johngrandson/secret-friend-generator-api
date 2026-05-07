"""Domain events for the Organization aggregate."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.tenancy.domain.role.value_objects import Role
from src.shared.events import DomainEvent


@dataclass(frozen=True)
class OrganizationCreated(DomainEvent):
    """Raised when a new organization is created with its initial owner."""

    organization_id: UUID
    name: str
    slug: str
    owner_user_id: UUID


@dataclass(frozen=True)
class MemberAdded(DomainEvent):
    """Raised when a user is added to an organization."""

    organization_id: UUID
    user_id: UUID
    role: Role


@dataclass(frozen=True)
class MemberRemoved(DomainEvent):
    """Raised when a user is removed from an organization."""

    organization_id: UUID
    user_id: UUID


@dataclass(frozen=True)
class MemberRoleChanged(DomainEvent):
    """Raised when a member's role is changed."""

    organization_id: UUID
    user_id: UUID
    old_role: Role
    new_role: Role
