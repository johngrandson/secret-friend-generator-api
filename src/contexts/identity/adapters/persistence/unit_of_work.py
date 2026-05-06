"""SQLAlchemyIdentityUnitOfWork — adapter implementing IIdentityUnitOfWork.

Holds a single AsyncSession and builds repository instances from it.
Satisfies IIdentityUnitOfWork structurally (no explicit inheritance).
"""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.identity.adapters.persistence.user.repository import (
    SQLAlchemyUserRepository,
)


class SQLAlchemyIdentityUnitOfWork:
    """SQLAlchemy-backed unit of work for the identity bounded context.

    The caller is responsible for passing a session scoped to the current
    request (typically via FastAPI's Depends(get_session)).

    Example::

        async with SQLAlchemyIdentityUnitOfWork(session) as uow:
            user = await uow.users.find_by_id(user_id)
            user.update_name("New Name")
            await uow.users.update(user)
            await uow.commit()
    """

    users: SQLAlchemyUserRepository

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = SQLAlchemyUserRepository(session)

    async def __aenter__(self) -> "SQLAlchemyIdentityUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self._session.rollback()
