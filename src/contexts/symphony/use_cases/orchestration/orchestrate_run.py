"""OrchestrateRunUseCase — drive a single Run through the symphony pipeline.

LOAD-BEARING INVARIANT (locked in F5): the orchestrator NEVER iterates
in-memory between sub-use-cases. Every loop iteration:

  1. Opens a fresh UoW context to re-read the Run state from persistence.
  2. Dispatches the matching sub-use-case based on ``run.status``.
  3. Sub-use-cases manage their own UoW + commit + publish.

This is what makes the pipeline crash-safe: a process killed mid-orchestration
resumes from the last committed state.

Pause states (SPEC_PENDING, PLAN_PENDING, RETRY_PENDING) return immediately
with ``OrchestrateOutcome.PAUSED`` — the caller (HTTP webhook, tick scheduler)
re-invokes after the relevant external event.

Use case is pure: it depends only on Protocols + sub-use-case Protocols
+ ``ISymphonyUnitOfWork``. The sub-use-cases themselves remain free of any
infrastructure import — orchestration just chains them.
"""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from src.contexts.symphony.domain.backlog.issue import Issue
from src.contexts.symphony.domain.constants import MAX_ORCHESTRATION_ITERATIONS
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.contexts.symphony.use_cases.run.execute import (
    ExecuteRunRequest,
    ExecuteRunUseCase,
)
from src.contexts.symphony.use_cases.run.open_pr import (
    OpenPRRequest,
    OpenPRUseCase,
)
from src.contexts.symphony.use_cases.run.run_gates import (
    RunGatesRequest,
    RunGatesUseCase,
)
from src.contexts.symphony.use_cases.plan.generate import (
    GeneratePlanRequest,
    GeneratePlanUseCase,
)
from src.contexts.symphony.use_cases.spec.generate import (
    GenerateSpecRequest,
    GenerateSpecUseCase,
)
from src.shared.event_publisher import IEventPublisher


class OrchestrateOutcome(StrEnum):
    """Terminal classes for one orchestrate call. Caller decides next-tick."""

    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class UnknownRunStatusError(Exception):
    """Run.status reached an enum value the orchestrator does not handle."""


@dataclass
class OrchestrationContext:
    """Workflow-derived primitives forwarded to sub-use-cases.

    Caller (F8 wiring or HTTP route) extracts these from
    ``WorkflowDefinition`` once and forwards verbatim. Keeps the use case
    free of Pydantic infrastructure imports while still letting it pass
    workflow-shaped data downstream.
    """

    issue: Issue
    execute_prompt_template: str
    model_name: str
    harness_config: object
    pr_branch: str
    pr_base_branch: str
    pr_title: str
    pr_is_draft: bool = True
    pr_labels: tuple[str, ...] = ()


@dataclass
class OrchestrateRunRequest:
    run_id: UUID
    context: OrchestrationContext


@dataclass
class OrchestrateRunResponse:
    run: RunDTO | None
    outcome: OrchestrateOutcome
    final_status: str
    paused_reason: str | None = None
    error_message: str | None = None


class OrchestrateRunUseCase:
    """Coordinator: chains the sub-use-cases, re-reading Run state every step."""

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
        self._generate_spec = generate_spec_use_case
        self._generate_plan = generate_plan_use_case
        self._execute_run = execute_run_use_case
        self._run_gates = run_gates_use_case
        self._open_pr = open_pr_use_case
        self._publisher = event_publisher

    async def execute(
        self, request: OrchestrateRunRequest
    ) -> OrchestrateRunResponse:
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
            status = run.status

            if status == RunStatus.GEN_SPEC:
                await self._generate_spec.execute(
                    GenerateSpecRequest(run_id=run.id, issue=ctx.issue)
                )
            elif status == RunStatus.SPEC_PENDING:
                return _paused(last_run_dto, "awaiting_spec_approval")
            elif status == RunStatus.SPEC_APPROVED:
                await self._generate_plan.execute(
                    GeneratePlanRequest(run_id=run.id, issue=ctx.issue)
                )
            elif status == RunStatus.PLAN_PENDING:
                return _paused(last_run_dto, "awaiting_plan_approval")
            elif status == RunStatus.PLAN_APPROVED:
                await self._execute_run.execute(
                    ExecuteRunRequest(
                        run_id=run.id,
                        issue=ctx.issue,
                        prompt_template=ctx.execute_prompt_template,
                        model_name=ctx.model_name,
                    )
                )
            elif status == RunStatus.RETRY_PENDING:
                return _paused(last_run_dto, "awaiting_retry")
            elif status == RunStatus.EXECUTED:
                await self._run_gates.execute(
                    RunGatesRequest(
                        run_id=run.id, harness_config=ctx.harness_config
                    )
                )
            elif status == RunStatus.GATES_PASSED:
                await self._open_pr.execute(
                    OpenPRRequest(
                        run_id=run.id,
                        issue=ctx.issue,
                        branch=ctx.pr_branch,
                        base_branch=ctx.pr_base_branch,
                        title=ctx.pr_title,
                        is_draft=ctx.pr_is_draft,
                        labels=ctx.pr_labels,
                    )
                )
            elif status == RunStatus.GATES_FAILED:
                final = await self._mark_failed(run.id, "gates_failed")
                return OrchestrateRunResponse(
                    final,
                    OrchestrateOutcome.FAILED,
                    final_status=RunStatus.FAILED.value,
                    error_message="gates_failed",
                )
            elif status in (RunStatus.DONE, RunStatus.PR_OPEN):
                return OrchestrateRunResponse(
                    last_run_dto,
                    OrchestrateOutcome.COMPLETED,
                    final_status=status.value,
                )
            elif status == RunStatus.FAILED:
                return OrchestrateRunResponse(
                    last_run_dto,
                    OrchestrateOutcome.FAILED,
                    final_status=status.value,
                    error_message=run.error,
                )
            else:
                raise UnknownRunStatusError(
                    f"Orchestrator does not handle status={status!r}"
                )

        return OrchestrateRunResponse(
            last_run_dto,
            OrchestrateOutcome.FAILED,
            final_status=last_run_dto.status if last_run_dto else "unknown",
            error_message=f"max_iterations_exceeded ({MAX_ORCHESTRATION_ITERATIONS})",
        )

    async def _mark_failed(self, run_id: UUID, reason: str) -> RunDTO | None:
        async with self._uow:
            run = await self._uow.runs.find_by_id(run_id)
            if run is None:
                return None
            run.mark_failed(reason)
            saved = await self._uow.runs.update(run)
            await self._uow.commit()
            events = run.pull_events()
        if events:
            await self._publisher.publish(events)
        return RunDTO.from_entity(saved)


def _paused(run: RunDTO, reason: str) -> OrchestrateRunResponse:
    return OrchestrateRunResponse(
        run,
        OrchestrateOutcome.PAUSED,
        final_status=run.status,
        paused_reason=reason,
    )
