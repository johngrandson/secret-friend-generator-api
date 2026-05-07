"""Sub-use-case wrapper handlers.

Each public method here delegates to a sub-use-case and normalises the
``SubResult`` (or ``ExecuteRunResponse``) into a uniform ``StepResult``.
``_run_sub_use_case`` extracts the repeated ``if not sub.success`` check
into a single helper used by every wrapper.
"""

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.use_cases.orchestration.dtos import (
    OrchestrationContext,
    StepAction,
    StepResult,
)
from src.contexts.symphony.use_cases.orchestration.protocols import SubResult
from src.contexts.symphony.use_cases.plan.generate import (
    GeneratePlanRequest,
    GeneratePlanUseCase,
)
from src.contexts.symphony.use_cases.run.execute import (
    ExecuteOutcome,
    ExecuteRunRequest,
    ExecuteRunUseCase,
)
from src.contexts.symphony.use_cases.run.open_pr import OpenPRRequest, OpenPRUseCase
from src.contexts.symphony.use_cases.run.run_gates import (
    RunGatesRequest,
    RunGatesUseCase,
)
from src.contexts.symphony.use_cases.spec.generate import (
    GenerateSpecRequest,
    GenerateSpecUseCase,
)


def _run_sub_use_case(result: SubResult, fallback_error: str) -> StepResult | None:
    """Return ``StepResult(FAILED)`` if ``result.success`` is false, else ``None``.

    Caller pattern: ``if step := _run_sub_use_case(...): return step``.
    """
    if not result.success:
        return StepResult(
            action=StepAction.FAILED,
            error_message=result.error_message or fallback_error,
        )
    return None


class SubUseCaseHandlers:
    """Handlers that delegate to sub-use-cases. Composed into OrchestrateRunUseCase."""

    def __init__(
        self,
        generate_spec: GenerateSpecUseCase,
        generate_plan: GeneratePlanUseCase,
        execute_run: ExecuteRunUseCase,
        run_gates: RunGatesUseCase,
        open_pr: OpenPRUseCase,
    ) -> None:
        self._generate_spec = generate_spec
        self._generate_plan = generate_plan
        self._execute_run = execute_run
        self._run_gates = run_gates
        self._open_pr = open_pr

    async def handle_gen_spec(
        self, run: Run, ctx: OrchestrationContext
    ) -> StepResult:
        result = await self._generate_spec.execute(
            GenerateSpecRequest(run_id=run.id, issue=ctx.issue)
        )
        if step := _run_sub_use_case(result, "gen_spec_failed"):
            return step
        return StepResult(action=StepAction.CONTINUE)

    async def handle_generate_plan(
        self, run: Run, ctx: OrchestrationContext
    ) -> StepResult:
        """Shared handler for SPEC_APPROVED and GEN_PLAN — both generate a plan."""
        result = await self._generate_plan.execute(
            GeneratePlanRequest(run_id=run.id, issue=ctx.issue)
        )
        if step := _run_sub_use_case(result, "gen_plan_failed"):
            return step
        return StepResult(action=StepAction.CONTINUE)

    async def handle_execute(
        self, run: Run, ctx: OrchestrationContext
    ) -> StepResult:
        result = await self._execute_run.execute(
            ExecuteRunRequest(
                run_id=run.id,
                issue=ctx.issue,
                prompt_template=ctx.execute_prompt_template,
                model_name=ctx.model_name,
            )
        )
        if result.outcome == ExecuteOutcome.FAILED:
            return StepResult(
                action=StepAction.FAILED,
                error_message=result.error_message or "execute_failed",
            )
        return StepResult(action=StepAction.CONTINUE)

    async def handle_run_gates(
        self, run: Run, ctx: OrchestrationContext
    ) -> StepResult:
        result = await self._run_gates.execute(
            RunGatesRequest(run_id=run.id, harness_config=ctx.harness_config)
        )
        if step := _run_sub_use_case(result, "gates_error"):
            return step
        return StepResult(action=StepAction.CONTINUE)

    async def handle_open_pr(
        self, run: Run, ctx: OrchestrationContext
    ) -> StepResult:
        result = await self._open_pr.execute(
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
        if step := _run_sub_use_case(result, "open_pr_failed"):
            return step
        return StepResult(action=StepAction.CONTINUE)
