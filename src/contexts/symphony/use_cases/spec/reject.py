"""RejectSpecUseCase — reject a pending spec version with a reason."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.event_publisher import IEventPublisher
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.spec.dto import SpecDTO


@dataclass
class RejectSpecRequest:
    spec_id: UUID
    reason: str


@dataclass
class RejectSpecResponse:
    spec: SpecDTO | None
    success: bool
    error_message: str | None = None


class RejectSpecUseCase:
    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: RejectSpecRequest) -> RejectSpecResponse:
        async with self._uow:
            spec = await self._uow.specs.find_by_id(request.spec_id)
            if spec is None:
                return RejectSpecResponse(None, False, "Spec not found.")
            try:
                spec.reject(reason=request.reason)
            except ValueError as exc:
                return RejectSpecResponse(None, False, str(exc))
            updated = await self._uow.specs.update(spec)
            await self._uow.commit()
            events = spec.pull_events()

        if events:  # pragma: no branch
            await self._publisher.publish(events)
        return RejectSpecResponse(SpecDTO.from_entity(updated), True)
