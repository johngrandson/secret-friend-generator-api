"""CreatePlanUseCase — orchestrates creation of a new plan version for a run."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.event_publisher import IEventPublisher
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.use_cases.plan.dto import PlanDTO


@dataclass
class CreatePlanRequest:
    run_id: UUID
    version: int
    content: str


@dataclass
class CreatePlanResponse:
    plan: PlanDTO | None
    success: bool
    error_message: str | None = None


class CreatePlanUseCase:
    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: CreatePlanRequest) -> CreatePlanResponse:
        try:
            plan = Plan.create(
                run_id=request.run_id,
                version=request.version,
                content=request.content,
            )
        except ValueError as exc:
            return CreatePlanResponse(None, False, str(exc))

        async with self._uow:
            saved = await self._uow.plans.save(plan)
            await self._uow.commit()
            events = plan.pull_events()

        if events:  # pragma: no branch
            await self._publisher.publish(events)
        return CreatePlanResponse(PlanDTO.from_entity(saved), True)
