"""OrchestrateRunUseCase — drive a single Run through the symphony pipeline.

LOAD-BEARING INVARIANT: the orchestrator NEVER iterates in-memory between
sub-use-cases. Every loop iteration re-reads the Run from persistence so
sub-use-cases commit independently and crash recovery is automatic.

State machine (status → action):
  GEN_SPEC        → GenerateSpecUseCase  → SPEC_PENDING
  SPEC_PENDING    → check latest Spec (approved/rejected/pending)
  SPEC_APPROVED   → GeneratePlanUseCase  → PLAN_PENDING
  GEN_PLAN        → GeneratePlanUseCase  (after rejection)
  PLAN_PENDING    → check latest Plan (approved/rejected/pending)
  PLAN_APPROVED   → ExecuteRunUseCase    → EXECUTED / RETRY_PENDING
  RETRY_PENDING   → pause "awaiting_retry"
  EXECUTED        → RunGatesUseCase      → GATES_PASSED / GATES_FAILED
  GATES_PASSED    → OpenPRUseCase        → PR_OPEN / DONE
  GATES_FAILED    → mark Run FAILED
  PR_OPEN / DONE  → COMPLETED
  FAILED          → terminal
  CANCELLED       → terminal

Design pattern: Strategy + Registry, with explicit composition.
  Handlers are split by behaviour:
    - handlers.sub_use_case_handlers — wraps each sub-use-case
    - handlers.verdict_check_handlers — spec/plan approval polling
    - handlers.terminal_handlers     — pure terminal/passive responses
  ``_handle_gates_failed`` stays here as the single hybrid case
  (needs persistence + returns StepResult).
  ``_dispatch`` maps RunStatus → handler. ``execute()`` runs the loop.
"""

from collections.abc import Callable, Coroutine
from typing import Any, Final, TypeAlias

from src.contexts.symphony.domain.constants import MAX_ORCHESTRATION_ITERATIONS
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.orchestration.dtos import (
    OrchestrateOutcome,
    OrchestrateRunRequest,
    OrchestrateRunResponse,
    OrchestrationContext,
    StepAction,
    StepResult,
    build_completed_response,
    build_failed_response,
    build_paused_response,
)
from src.contexts.symphony.use_cases.orchestration.handlers import (
    SubUseCaseHandlers,
    VerdictCheckHandlers,
    handle_cancelled_terminal,
    handle_completed,
    handle_failed_terminal,
    handle_retry_pending,
)
from src.contexts.symphony.use_cases.orchestration.run_persistence_service import (
    RunPersistenceService,
)
from src.contexts.symphony.use_cases.plan.generate import GeneratePlanUseCase
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.contexts.symphony.use_cases.run.execute import ExecuteRunUseCase
from src.contexts.symphony.use_cases.run.open_pr import OpenPRUseCase
from src.contexts.symphony.use_cases.run.run_gates import RunGatesUseCase
from src.contexts.symphony.use_cases.spec.generate import GenerateSpecUseCase
from src.shared.event_publisher import IEventPublisher

# Statuses owned by sub-use-cases as transient states, or entry-point
# statuses not seen by the dispatch loop.
_UNREACHABLE_STATUSES: Final[frozenset[RunStatus]] = frozenset(
    {RunStatus.RECEIVED, RunStatus.EXECUTE, RunStatus.GATES}
)

# Type for each handler entry in the dispatch table.
_StepHandler: TypeAlias = Callable[..., Coroutine[Any, Any, Any]]


class UnknownRunStatusError(Exception):
    """Run.status reached an enum value the orchestrator does not handle."""


class OrchestrateRunUseCase:
    """Coordinator: chains sub-use-cases, re-reading Run state each step.

    The ``_dispatch`` dict is the state-machine table. Reading it is
    equivalent to reading the module-level docstring state-machine spec.
    Handlers are composed from focused modules under ``handlers/``.
    """

    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        generate_spec_use_case: GenerateSpecUseCase,
        generate_plan_use_case: GeneratePlanUseCase,
        execute_run_use_case: ExecuteRunUseCase,
        run_gates_use_case: RunGatesUseCase,
        open_pr_use_case: OpenPRUseCase,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._persistence = RunPersistenceService(uow=uow, publisher=event_publisher)

        sub_handlers = SubUseCaseHandlers(
            generate_spec=generate_spec_use_case,
            generate_plan=generate_plan_use_case,
            execute_run=execute_run_use_case,
            run_gates=run_gates_use_case,
            open_pr=open_pr_use_case,
        )
        verdict_handlers = VerdictCheckHandlers(uow=uow, persistence=self._persistence)

        # Strategy + Registry: one entry per handled RunStatus.
        # SPEC_APPROVED and GEN_PLAN share the same handler (both generate a plan).
        self._dispatch: dict[RunStatus, _StepHandler] = {
            RunStatus.GEN_SPEC: sub_handlers.handle_gen_spec,
            RunStatus.SPEC_PENDING: verdict_handlers.handle_spec_pending,
            RunStatus.SPEC_APPROVED: sub_handlers.handle_generate_plan,
            RunStatus.GEN_PLAN: sub_handlers.handle_generate_plan,
            RunStatus.PLAN_PENDING: verdict_handlers.handle_plan_pending,
            RunStatus.PLAN_APPROVED: sub_handlers.handle_execute,
            RunStatus.RETRY_PENDING: handle_retry_pending,
            RunStatus.EXECUTED: sub_handlers.handle_run_gates,
            RunStatus.GATES_PASSED: sub_handlers.handle_open_pr,
            RunStatus.GATES_FAILED: self._handle_gates_failed,
            RunStatus.PR_OPEN: handle_completed,
            RunStatus.DONE: handle_completed,
            RunStatus.FAILED: handle_failed_terminal,
            RunStatus.CANCELLED: handle_cancelled_terminal,
        }

        # Structural guarantee: every RunStatus is dispatched or explicitly
        # acknowledged as unreachable.
        _covered = frozenset(self._dispatch) | _UNREACHABLE_STATUSES
        _missing = frozenset(RunStatus) - _covered
        if _missing:
            raise RuntimeError(
                f"OrchestrateRunUseCase dispatch table is incomplete. "
                f"Unhandled statuses: {_missing!r}. "
                "Add a handler or add to _UNREACHABLE_STATUSES."
            )

    async def _handle_gates_failed(
        self,
        run: Run,
        ctx: OrchestrationContext,  # noqa: ARG002
    ) -> StepResult:
        """Hybrid handler: persists FAILED status and returns terminal StepResult."""
        await self._persistence.mark_failed(run.id, "gates_failed")
        return StepResult(
            action=StepAction.FAILED,
            final_status=RunStatus.FAILED.value,
            error_message="gates_failed",
        )

    async def execute(self, request: OrchestrateRunRequest) -> OrchestrateRunResponse:
        """Drive the Run state machine until pause, completion, or failure."""
        ctx = request.context
        last_run_dto: RunDTO | None = None

        for _ in range(MAX_ORCHESTRATION_ITERATIONS):
            async with self._uow:
                run = await self._uow.runs.find_by_id(request.run_id)
            if run is None:
                return OrchestrateRunResponse(
                    None,
                    OrchestrateOutcome.FAILED,
                    final_status="missing",
                    error_message="Run not found.",
                )
            last_run_dto = RunDTO.from_entity(run)

            handler = self._dispatch.get(run.status)
            if handler is None:
                raise UnknownRunStatusError(
                    f"Orchestrator does not handle status={run.status!r}"
                )

            result = await handler(run, ctx)

            match result.action:
                case StepAction.CONTINUE:
                    continue
                case StepAction.PAUSED:
                    return build_paused_response(
                        last_run_dto, result.paused_reason or "unknown"
                    )
                case StepAction.COMPLETED:
                    return build_completed_response(
                        last_run_dto, result.final_status or run.status.value
                    )
                case StepAction.FAILED:
                    return build_failed_response(
                        last_run_dto,
                        result.error_message or "failed",
                        final_status=result.final_status,
                    )

        return OrchestrateRunResponse(
            last_run_dto,
            OrchestrateOutcome.FAILED,
            final_status=last_run_dto.status if last_run_dto else "unknown",
            error_message=f"max_iterations_exceeded ({MAX_ORCHESTRATION_ITERATIONS})",
        )
