"""CreateSpecUseCase — orchestrates creation of a new spec version for a run."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.event_publisher import IEventPublisher
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.use_cases.spec.dto import SpecDTO


@dataclass
class CreateSpecRequest:
    run_id: UUID
    version: int
    content: str


@dataclass
class CreateSpecResponse:
    spec: SpecDTO | None
    success: bool
    error_message: str | None = None


class CreateSpecUseCase:
    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: CreateSpecRequest) -> CreateSpecResponse:
        try:
            spec = Spec.create(
                run_id=request.run_id,
                version=request.version,
                content=request.content,
            )
        except ValueError as exc:
            return CreateSpecResponse(None, False, str(exc))

        async with self._uow:
            saved = await self._uow.specs.save(spec)
            await self._uow.commit()
            events = spec.pull_events()

        if events:  # pragma: no branch
            await self._publisher.publish(events)
        return CreateSpecResponse(SpecDTO.from_entity(saved), True)
