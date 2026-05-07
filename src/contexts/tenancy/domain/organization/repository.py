"""IOrganizationRepository — output port (Protocol) for Organization persistence.

Structural typing: any class with these methods satisfies the contract.
No inheritance required from concrete adapters.
"""

from typing import Protocol, runtime_checkable
from uuid import UUID

from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.value_objects import Slug


@runtime_checkable
class IOrganizationRepository(Protocol):
    async def find_by_id(self, organization_id: UUID) -> Organization | None: ...

    async def find_by_slug(self, slug: Slug) -> Organization | None: ...

    async def list_for_user(self, user_id: UUID) -> list[Organization]: ...

    async def save(self, organization: Organization) -> Organization: ...

    async def update(self, organization: Organization) -> Organization: ...

    async def delete(self, organization_id: UUID) -> bool: ...
