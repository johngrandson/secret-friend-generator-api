"""GetRunDetailUseCase — return Run + latest Spec + latest Plan in one round-trip.

Aggregate query for the operator UI. Read-only; opens a single UoW
context and pulls the three entities once. AgentSession / GateResult /
PullRequest are not yet wired in the persistence layer (Phase 09 work).
"""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.plan.dto import PlanDTO
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.contexts.symphony.use_cases.spec.dto import SpecDTO


@dataclass
class GetRunDetailRequest:
    run_id: UUID


@dataclass
class GetRunDetailResponse:
    run: RunDTO | None
    latest_spec: SpecDTO | None
    latest_plan: PlanDTO | None
    success: bool
    error_message: str | None = None


class GetRunDetailUseCase:
    def __init__(self, uow: ISymphonyUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, request: GetRunDetailRequest) -> GetRunDetailResponse:
        async with self._uow:
            run = await self._uow.runs.find_by_id(request.run_id)
            if run is None:
                return GetRunDetailResponse(
                    run=None,
                    latest_spec=None,
                    latest_plan=None,
                    success=False,
                    error_message="Run not found.",
                )
            spec = await self._uow.specs.find_latest_for_run(request.run_id)
            plan = await self._uow.plans.find_latest_for_run(request.run_id)

        return GetRunDetailResponse(
            run=RunDTO.from_entity(run),
            latest_spec=SpecDTO.from_entity(spec) if spec else None,
            latest_plan=PlanDTO.from_entity(plan) if plan else None,
            success=True,
        )
