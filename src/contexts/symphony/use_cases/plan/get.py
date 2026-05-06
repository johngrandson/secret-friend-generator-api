"""GetPlanUseCase — fetch a single plan by id."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.plan.dto import PlanDTO


@dataclass
class GetPlanRequest:
    plan_id: UUID


@dataclass
class GetPlanResponse:
    plan: PlanDTO | None
    success: bool
    error_message: str | None = None


class GetPlanUseCase:
    def __init__(self, uow: ISymphonyUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, request: GetPlanRequest) -> GetPlanResponse:
        async with self._uow:
            plan = await self._uow.plans.find_by_id(request.plan_id)
        if plan is None:
            return GetPlanResponse(None, False, "Plan not found.")
        return GetPlanResponse(PlanDTO.from_entity(plan), True)
