"""RunPersistenceService — isolated infra for persisting Run state changes.

Encapsulates the "set status / mark failed → commit → publish events"
pattern used by the orchestration handlers. Extracted from the previous
``_promote_run`` / ``_mark_failed`` mixin methods so handlers can depend
on a focused service instead of inheriting infrastructure.
"""

from uuid import UUID

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.shared.event_publisher import IEventPublisher


class RunPersistenceService:
    """Persists Run state transitions and publishes the resulting events."""

    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = publisher

    async def promote_run(self, run: Run, new_status: RunStatus) -> None:
        """Transition Run to ``new_status``, persist, commit, publish events."""
        run.set_status(new_status)
        async with self._uow:
            await self._uow.runs.update(run)
            await self._uow.commit()
        events = run.pull_events()
        if events:
            await self._publisher.publish(events)

    async def mark_failed(self, run_id: UUID, reason: str) -> RunDTO | None:
        """Persist FAILED status on the Run and publish RunFailed event.

        Returns the updated RunDTO, or ``None`` if the Run is no longer found.
        """
        async with self._uow:
            run = await self._uow.runs.find_by_id(run_id)
            if run is None:
                return None
            run.mark_failed(reason)
            saved = await self._uow.runs.update(run)
            await self._uow.commit()
            events = run.pull_events()
        if events:
            await self._publisher.publish(events)
        return RunDTO.from_entity(saved)
