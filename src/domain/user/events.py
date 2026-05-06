"""Domain events for the User aggregate."""

from dataclasses import dataclass
from uuid import UUID

from src.domain._shared.events import DomainEvent


@dataclass(frozen=True)
class UserCreated(DomainEvent):
    """Raised when a new user is successfully created."""

    user_id: UUID
    email: str
    name: str


@dataclass(frozen=True)
class UserDeactivated(DomainEvent):
    """Raised when a user is deactivated."""

    user_id: UUID


@dataclass(frozen=True)
class UserUpdated(DomainEvent):
    """Raised when a user's mutable fields are changed."""

    user_id: UUID


@dataclass(frozen=True)
class UserDeleted(DomainEvent):
    """Raised when a user is permanently removed."""

    user_id: UUID
