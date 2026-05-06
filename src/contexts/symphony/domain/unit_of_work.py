"""ISymphonyUnitOfWork — output port for atomic symphony context transactions.

Protocol lives in the domain layer so use cases depend on an abstraction,
not on SQLAlchemy. The adapter (SQLAlchemySymphonyUnitOfWork) lives in the
persistence adapter layer and satisfies this protocol structurally.
"""

from types import TracebackType
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.contexts.symphony.domain.run.repository import IRunRepository
    from src.contexts.symphony.domain.spec.repository import ISpecRepository
    from src.contexts.symphony.domain.plan.repository import IPlanRepository


@runtime_checkable
class ISymphonyUnitOfWork(Protocol):
    """Transactional boundary for the symphony bounded context.

    Usage::

        async with uow:
            run = await uow.runs.find_by_id(run_id)
            spec = await uow.specs.save(spec)
            await uow.commit()
    """

    runs: "IRunRepository"
    specs: "ISpecRepository"
    plans: "IPlanRepository"

    async def __aenter__(self) -> "ISymphonyUnitOfWork": ...

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
