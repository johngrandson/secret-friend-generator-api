"""IIdentityUnitOfWork — output port for atomic identity context transactions.

Protocol lives in the domain layer so use cases depend on an abstraction,
not on SQLAlchemy. The adapter (SQLAlchemyIdentityUnitOfWork) lives in the
persistence adapter layer and satisfies this protocol structurally.
"""

from types import TracebackType
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.contexts.identity.domain.user.repository import IUserRepository


@runtime_checkable
class IIdentityUnitOfWork(Protocol):
    """Transactional boundary for the identity bounded context.

    Usage::

        async with uow:
            user = await uow.users.find_by_id(user_id)
            user.update_name("New Name")
            await uow.users.update(user)
            await uow.commit()
    """

    users: "IUserRepository"

    async def __aenter__(self) -> "IIdentityUnitOfWork": ...

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
