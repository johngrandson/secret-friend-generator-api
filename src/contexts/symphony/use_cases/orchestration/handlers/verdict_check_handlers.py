"""Verdict-check handlers for SPEC_PENDING and PLAN_PENDING.

Both handlers follow the same shape: read latest artifact, inspect its
``verdict()``, then promote the Run or pause. ``_check_verdict`` extracts
the shared structure so each public handler is reduced to data-binding.
"""

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.orchestration.dtos import (
    OrchestrationContext,
    StepAction,
    StepResult,
)
from src.contexts.symphony.use_cases.orchestration.paused_reason_constants import (
    REASON_AWAITING_PLAN_APPROVAL,
    REASON_AWAITING_SPEC_APPROVAL,
    REASON_NO_PLAN_FOUND,
    REASON_NO_SPEC_FOUND,
)
from src.contexts.symphony.use_cases.orchestration.protocols import Verdictable
from src.contexts.symphony.use_cases.orchestration.run_persistence_service import (
    RunPersistenceService,
)


class VerdictCheckHandlers:
    """Handlers that read an approval artifact and promote Run by verdict."""

    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        persistence: RunPersistenceService,
    ) -> None:
        self._uow = uow
        self._persistence = persistence

    async def _check_verdict(
        self,
        run: Run,
        artifact: Verdictable | None,
        *,
        approved_status: RunStatus,
        rejected_status: RunStatus,
        awaiting_reason: str,
        not_found_reason: str,
    ) -> StepResult:
        if artifact is None:
            return StepResult(action=StepAction.PAUSED, paused_reason=not_found_reason)
        match artifact.verdict():
            case "approved":
                await self._persistence.promote_run(run, approved_status)
                return StepResult(action=StepAction.CONTINUE)
            case "rejected":
                await self._persistence.promote_run(run, rejected_status)
                return StepResult(action=StepAction.CONTINUE)
            case "pending":
                return StepResult(
                    action=StepAction.PAUSED, paused_reason=awaiting_reason
                )
            case _:
                return StepResult(
                    action=StepAction.PAUSED, paused_reason=awaiting_reason
                )

    async def handle_spec_pending(
        self,
        run: Run,
        ctx: OrchestrationContext,  # noqa: ARG002
    ) -> StepResult:
        async with self._uow:
            spec = await self._uow.specs.find_latest_for_run(run.id)
        return await self._check_verdict(
            run,
            spec,
            approved_status=RunStatus.SPEC_APPROVED,
            rejected_status=RunStatus.GEN_SPEC,
            awaiting_reason=REASON_AWAITING_SPEC_APPROVAL,
            not_found_reason=REASON_NO_SPEC_FOUND,
        )

    async def handle_plan_pending(
        self,
        run: Run,
        ctx: OrchestrationContext,  # noqa: ARG002
    ) -> StepResult:
        async with self._uow:
            plan = await self._uow.plans.find_latest_for_run(run.id)
        return await self._check_verdict(
            run,
            plan,
            approved_status=RunStatus.PLAN_APPROVED,
            rejected_status=RunStatus.GEN_PLAN,
            awaiting_reason=REASON_AWAITING_PLAN_APPROVAL,
            not_found_reason=REASON_NO_PLAN_FOUND,
        )
