"""SQLAlchemyTenancyUnitOfWork — adapter implementing ITenancyUnitOfWork.

Holds a single AsyncSession and builds repository instances from it.
Satisfies ITenancyUnitOfWork structurally (no explicit inheritance).
"""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.tenancy.adapters.persistence.organization.repository import (
    SQLAlchemyOrganizationRepository,
)


class SQLAlchemyTenancyUnitOfWork:
    """SQLAlchemy-backed unit of work for the tenancy bounded context.

    The caller is responsible for passing a session scoped to the current
    request (typically via FastAPI's Depends(get_session)).

    Example::

        async with SQLAlchemyTenancyUnitOfWork(session) as uow:
            org = await uow.organizations.find_by_id(org_id)
            org.add_member(user_id, Role.MEMBER)
            await uow.organizations.update(org)
            await uow.commit()
    """

    organizations: SQLAlchemyOrganizationRepository

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.organizations = SQLAlchemyOrganizationRepository(session)

    async def __aenter__(self) -> "SQLAlchemyTenancyUnitOfWork":
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
