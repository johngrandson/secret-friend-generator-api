"""Organization entity — aggregate root for the tenancy context.

Holds a name, slug, and a set of memberships. Invariant: there is always at
least one OWNER. Mutations that would violate this invariant raise ValueError.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.contexts.tenancy.domain.organization.events import (
    MemberAdded,
    MemberRemoved,
    MemberRoleChanged,
    OrganizationCreated,
)
from src.contexts.tenancy.domain.organization.value_objects import (
    Membership,
    Slug,
)
from src.contexts.tenancy.domain.role.value_objects import Role
from src.shared.aggregate_root import AggregateRoot


@dataclass
class Organization(AggregateRoot):
    """Aggregate root binding a tenant identity to its members and roles."""

    name: str
    slug: Slug
    members: set[Membership] = field(default_factory=set)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ---------------- queries ----------------

    def find_member(self, user_id: UUID) -> Membership | None:
        """Return the Membership for a user, or None if they are not a member."""
        for m in self.members:
            if m.user_id == user_id:
                return m
        return None

    def has_member(self, user_id: UUID) -> bool:
        return self.find_member(user_id) is not None

    def owner_count(self) -> int:
        return sum(1 for m in self.members if m.role is Role.OWNER)

    # ---------------- mutations ----------------

    def add_member(self, user_id: UUID, role: Role) -> None:
        """Add a user with the given role. Raises if user already a member."""
        if self.has_member(user_id):
            raise ValueError(f"User {user_id} is already a member.")
        self.members.add(Membership(user_id=user_id, role=role))
        self.collect_event(
            MemberAdded(organization_id=self.id, user_id=user_id, role=role)
        )

    def remove_member(self, user_id: UUID) -> None:
        """Remove a user. Raises if user not a member or removing last OWNER."""
        existing = self.find_member(user_id)
        if existing is None:
            raise ValueError(f"User {user_id} is not a member.")
        if existing.role is Role.OWNER and self.owner_count() == 1:
            raise ValueError("Cannot remove the last OWNER of the organization.")
        self.members.discard(existing)
        self.collect_event(MemberRemoved(organization_id=self.id, user_id=user_id))

    def change_member_role(self, user_id: UUID, new_role: Role) -> None:
        """Change a member's role. Raises if not a member or downgrading last OWNER."""
        existing = self.find_member(user_id)
        if existing is None:
            raise ValueError(f"User {user_id} is not a member.")
        if existing.role is new_role:
            return  # no-op, no event emitted
        if (
            existing.role is Role.OWNER
            and new_role is not Role.OWNER
            and self.owner_count() == 1
        ):
            raise ValueError("Cannot demote the last OWNER of the organization.")
        self.members.discard(existing)
        self.members.add(Membership(user_id=user_id, role=new_role))
        self.collect_event(
            MemberRoleChanged(
                organization_id=self.id,
                user_id=user_id,
                old_role=existing.role,
                new_role=new_role,
            )
        )

    # ---------------- factory ----------------

    @classmethod
    def create(cls, name: str, slug: Slug, owner_user_id: UUID) -> "Organization":
        """Factory — enforces non-blank name and seeds the initial OWNER."""
        if not name.strip():
            raise ValueError("Organization name must not be blank.")
        org = cls(
            name=name,
            slug=slug,
            members={Membership(user_id=owner_user_id, role=Role.OWNER)},
        )
        org.collect_event(
            OrganizationCreated(
                organization_id=org.id,
                name=name,
                slug=str(slug),
                owner_user_id=owner_user_id,
            )
        )
        return org
