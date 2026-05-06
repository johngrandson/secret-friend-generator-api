"""ApproveSpecUseCase — approve a pending spec version."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.event_publisher import IEventPublisher
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.spec.dto import SpecDTO


@dataclass
class ApproveSpecRequest:
    spec_id: UUID
    approved_by: str


@dataclass
class ApproveSpecResponse:
    spec: SpecDTO | None
    success: bool
    error_message: str | None = None


class ApproveSpecUseCase:
    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: ApproveSpecRequest) -> ApproveSpecResponse:
        async with self._uow:
            spec = await self._uow.specs.find_by_id(request.spec_id)
            if spec is None:
                return ApproveSpecResponse(None, False, "Spec not found.")
            try:
                spec.approve(by=request.approved_by)
            except ValueError as exc:
                return ApproveSpecResponse(None, False, str(exc))
            updated = await self._uow.specs.update(spec)
            await self._uow.commit()
            events = spec.pull_events()

        if events:  # pragma: no branch
            await self._publisher.publish(events)
        return ApproveSpecResponse(SpecDTO.from_entity(updated), True)
