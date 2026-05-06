"""RejectPlanUseCase — reject a pending plan version with a reason."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.event_publisher import IEventPublisher
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.plan.dto import PlanDTO


@dataclass
class RejectPlanRequest:
    plan_id: UUID
    reason: str


@dataclass
class RejectPlanResponse:
    plan: PlanDTO | None
    success: bool
    error_message: str | None = None


class RejectPlanUseCase:
    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: RejectPlanRequest) -> RejectPlanResponse:
        async with self._uow:
            plan = await self._uow.plans.find_by_id(request.plan_id)
            if plan is None:
                return RejectPlanResponse(None, False, "Plan not found.")
            try:
                plan.reject(reason=request.reason)
            except ValueError as exc:
                return RejectPlanResponse(None, False, str(exc))
            updated = await self._uow.plans.update(plan)
            await self._uow.commit()
            events = plan.pull_events()

        if events:  # pragma: no branch
            await self._publisher.publish(events)
        return RejectPlanResponse(PlanDTO.from_entity(updated), True)
