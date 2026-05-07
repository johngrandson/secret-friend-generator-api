"""Value objects for the Organization aggregate.

- Slug: URL-safe organization identifier (lowercase, alnum, hyphens).
- Membership: immutable (user_id, role) pair attached to an organization.
"""

import re
from dataclasses import dataclass
from uuid import UUID

from src.contexts.tenancy.domain.role.value_objects import Role


_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


@dataclass(frozen=True)
class Slug:
    """URL-safe organization identifier (lowercase alnum + hyphens, 1-64 chars)."""

    value: str

    def __post_init__(self) -> None:
        if not _SLUG_RE.match(self.value):
            raise ValueError(
                "Slug must be 1-64 chars, lowercase alphanumeric and hyphens, "
                "not starting or ending with a hyphen."
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Membership:
    """Immutable association of a user to an organization with a role."""

    user_id: UUID
    role: Role
