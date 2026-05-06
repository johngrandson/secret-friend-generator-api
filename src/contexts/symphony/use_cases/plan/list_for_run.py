"""ListPlansForRunUseCase — return all plan versions for a given run."""

from dataclasses import dataclass, field
from uuid import UUID

from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.plan.dto import PlanDTO


@dataclass
class ListPlansForRunRequest:
    run_id: UUID


@dataclass
class ListPlansForRunResponse:
    plans: list[PlanDTO] = field(default_factory=list)
    success: bool = True
    error_message: str | None = None


class ListPlansForRunUseCase:
    def __init__(self, uow: ISymphonyUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, request: ListPlansForRunRequest) -> ListPlansForRunResponse:
        async with self._uow:
            plans = await self._uow.plans.list_by_run(request.run_id)
        return ListPlansForRunResponse(plans=[PlanDTO.from_entity(p) for p in plans])
