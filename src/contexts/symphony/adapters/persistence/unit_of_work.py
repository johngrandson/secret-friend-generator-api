"""SQLAlchemySymphonyUnitOfWork — adapter implementing ISymphonyUnitOfWork.

Holds a single AsyncSession and builds repository instances from it.
Satisfies ISymphonyUnitOfWork structurally (no explicit inheritance).
"""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.symphony.adapters.persistence.run.repository import (
    SQLAlchemyRunRepository,
)
from src.contexts.symphony.adapters.persistence.spec.repository import (
    SQLAlchemySpecRepository,
)
from src.contexts.symphony.adapters.persistence.plan.repository import (
    SQLAlchemyPlanRepository,
)


class SQLAlchemySymphonyUnitOfWork:
    """SQLAlchemy-backed unit of work for the symphony bounded context.

    The caller is responsible for passing a session scoped to the current
    request (typically via FastAPI's Depends(get_session)).

    Example::

        async with SQLAlchemySymphonyUnitOfWork(session) as uow:
            run = await uow.runs.find_by_id(run_id)
            spec = await uow.specs.save(spec)
            await uow.commit()
    """

    runs: SQLAlchemyRunRepository
    specs: SQLAlchemySpecRepository
    plans: SQLAlchemyPlanRepository

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.runs = SQLAlchemyRunRepository(session)
        self.specs = SQLAlchemySpecRepository(session)
        self.plans = SQLAlchemyPlanRepository(session)

    async def __aenter__(self) -> "SQLAlchemySymphonyUnitOfWork":
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
