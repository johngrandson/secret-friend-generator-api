"""IUserRepository — output port (Protocol) for User persistence.

Structural typing: any class with these methods satisfies the contract.
No inheritance required from concrete adapters.
"""

from typing import Optional, Protocol, runtime_checkable
from uuid import UUID

from src.domain.user.entity import User
from src.domain.user.email import Email


@runtime_checkable
class IUserRepository(Protocol):
    async def find_by_id(self, user_id: UUID) -> Optional[User]: ...
    async def find_by_email(self, email: Email) -> Optional[User]: ...
    async def list(self, limit: int = 20, offset: int = 0) -> list[User]: ...
    async def save(self, user: User) -> User: ...
    async def update(self, user: User) -> User: ...
    async def delete(self, user_id: UUID) -> bool: ...
