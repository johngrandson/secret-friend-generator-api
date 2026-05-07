"""Terminal/passive handlers — pure functions with no I/O dependencies.

Each handler maps a terminal RunStatus to a StepResult without reading
or writing persistence. Kept as module-level ``async def`` (the dispatch
loop awaits every handler uniformly) but no ``await`` is performed.
"""

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.use_cases.orchestration.dtos import (
    OrchestrationContext,
    StepAction,
    StepResult,
)
from src.contexts.symphony.use_cases.orchestration.paused_reason_constants import (
    REASON_AWAITING_RETRY,
)


async def handle_retry_pending(
    run: Run,  # noqa: ARG001
    ctx: OrchestrationContext,  # noqa: ARG001
) -> StepResult:
    return StepResult(action=StepAction.PAUSED, paused_reason=REASON_AWAITING_RETRY)


async def handle_completed(
    run: Run,
    ctx: OrchestrationContext,  # noqa: ARG001
) -> StepResult:
    return StepResult(action=StepAction.COMPLETED, final_status=run.status.value)


async def handle_failed_terminal(
    run: Run,
    ctx: OrchestrationContext,  # noqa: ARG001
) -> StepResult:
    return StepResult(
        action=StepAction.FAILED,
        final_status=run.status.value,
        error_message=run.error,
    )


async def handle_cancelled_terminal(
    run: Run,
    ctx: OrchestrationContext,  # noqa: ARG001
) -> StepResult:
    return StepResult(
        action=StepAction.FAILED,
        final_status=run.status.value,
        error_message=run.error or "cancelled by operator",
    )
