"""ITenancyUnitOfWork — output port for atomic tenancy context transactions.

Protocol lives in the domain layer so use cases depend on an abstraction,
not on SQLAlchemy. The adapter (SQLAlchemyTenancyUnitOfWork) lives in the
persistence adapter layer and satisfies this protocol structurally.
"""

from types import TracebackType
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.contexts.tenancy.domain.organization.repository import (
        IOrganizationRepository,
    )


@runtime_checkable
class ITenancyUnitOfWork(Protocol):
    """Transactional boundary for the tenancy bounded context.

    Usage::

        async with uow:
            org = await uow.organizations.find_by_id(org_id)
            org.add_member(user_id, Role.MEMBER)
            await uow.organizations.update(org)
            await uow.commit()
    """

    organizations: "IOrganizationRepository"

    async def __aenter__(self) -> "ITenancyUnitOfWork": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None:
        """Flush pending changes to the database and mark the transaction done."""
        ...

    async def rollback(self) -> None:
        """Discard all pending changes."""
        ...
