"""IUserRepository — output port (Protocol) for User persistence.

Structural typing: any class with these methods satisfies the contract.
No inheritance required from concrete adapters.
"""

from typing import Protocol, runtime_checkable
from uuid import UUID

from src.contexts.identity.domain.user.entity import User
from src.contexts.identity.domain.user.email import Email


@runtime_checkable
class IUserRepository(Protocol):
    async def find_by_id(self, user_id: UUID) -> User | None: ...

    """Find a user by their ID."""

    async def find_by_email(self, email: Email) -> User | None: ...

    """Find a user by their email."""

    async def list(self, limit: int = 20, offset: int = 0) -> list[User]: ...

    """List users with pagination."""

    async def save(self, user: User) -> User: ...

    """Save a new user."""

    async def update(self, user: User) -> User: ...

    """Update an existing user."""

    async def delete(self, user_id: UUID) -> bool: ...

    """Delete a user by their ID."""
