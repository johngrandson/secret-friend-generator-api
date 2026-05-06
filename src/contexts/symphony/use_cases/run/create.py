"""CreateRunUseCase — orchestrates creation of a new pipeline run."""

from dataclasses import dataclass

from src.shared.event_publisher import IEventPublisher
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.use_cases.run.dto import RunDTO


@dataclass
class CreateRunRequest:
    issue_id: str


@dataclass
class CreateRunResponse:
    run: RunDTO | None
    success: bool
    error_message: str | None = None


class CreateRunUseCase:
    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: CreateRunRequest) -> CreateRunResponse:
        try:
            run = Run.create(issue_id=request.issue_id)
        except ValueError as exc:
            return CreateRunResponse(None, False, str(exc))

        async with self._uow:
            saved = await self._uow.runs.save(run)
            await self._uow.commit()
            events = run.pull_events()

        if events:  # pragma: no branch
            await self._publisher.publish(events)
        return CreateRunResponse(RunDTO.from_entity(saved), True)
