"""UserDTO — use-case-layer data transfer object for User responses."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.identity.domain.user.entity import User


@dataclass(frozen=True)
class UserDTO:
    """Immutable snapshot of a User for use-case responses."""

    id: UUID
    email: str
    name: str
    is_active: bool

    @classmethod
    def from_entity(cls, user: User) -> "UserDTO":
        """Build a UserDTO from a User aggregate."""
        return cls(
            id=user.id,
            email=str(user.email),
            name=user.name,
            is_active=user.is_active,
        )
