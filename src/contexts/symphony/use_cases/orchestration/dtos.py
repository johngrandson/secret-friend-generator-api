"""DTOs and outcome types for the orchestration use case.

All data structures exchanged between the orchestrator and its callers
(HTTP routes, tests, containers) live here. Keeping them separate from the
state-machine logic allows imports without pulling in the full use-case graph.
"""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from src.contexts.symphony.domain.backlog.issue import Issue
from src.contexts.symphony.domain.harness_config import HarnessConfig
from src.contexts.symphony.use_cases.run.dto import RunDTO


class OrchestrateOutcome(StrEnum):
    """Terminal classes for one orchestrate call. Caller decides next-tick."""

    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class StepAction(StrEnum):
    """What the orchestrator does after a state-handler returns."""

    CONTINUE = "continue"  # re-read Run, dispatch next handler
    PAUSED = "paused"  # return PAUSED response to caller
    COMPLETED = "completed"  # terminal success
    FAILED = "failed"  # terminal failure


@dataclass(frozen=True)
class StepResult:
    """Outcome of one state-machine step. Discriminated by ``action``.

    All private ``_handle_*`` methods return this uniform type so the
    dispatch loop needs no special-case logic per handler.
    """

    action: StepAction
    final_status: str | None = None  # populated for COMPLETED/FAILED
    paused_reason: str | None = None  # populated for PAUSED
    error_message: str | None = None  # populated for FAILED


@dataclass
class OrchestrationContext:
    """Workflow-derived primitives forwarded to sub-use-cases.

    Caller (F8 wiring or HTTP route) extracts these from
    ``WorkflowDefinition`` once and forwards verbatim. ``harness_config``
    is the runtime domain VO — the HTTP route projects the Pydantic
    schema onto it before constructing the context.
    """

    issue: Issue
    execute_prompt_template: str
    model_name: str
    harness_config: HarnessConfig
    pr_branch: str
    pr_base_branch: str
    pr_title: str
    pr_is_draft: bool = True
    pr_labels: tuple[str, ...] = ()


@dataclass
class OrchestrateRunRequest:
    """Input DTO for one orchestration tick."""

    run_id: UUID
    context: OrchestrationContext


@dataclass
class OrchestrateRunResponse:
    """Output DTO. ``paused_reason`` is set when ``outcome == PAUSED``."""

    run: RunDTO | None
    outcome: OrchestrateOutcome
    final_status: str
    paused_reason: str | None = None
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Response builders — testable without importing the full use-case graph
# ---------------------------------------------------------------------------


def build_paused_response(run: RunDTO, reason: str) -> OrchestrateRunResponse:
    return OrchestrateRunResponse(
        run, OrchestrateOutcome.PAUSED, final_status=run.status, paused_reason=reason
    )


def build_completed_response(run: RunDTO, final_status: str) -> OrchestrateRunResponse:
    return OrchestrateRunResponse(
        run, OrchestrateOutcome.COMPLETED, final_status=final_status
    )


def build_failed_response(
    run: RunDTO | None,
    error: str,
    *,
    final_status: str | None = None,
) -> OrchestrateRunResponse:
    return OrchestrateRunResponse(
        run,
        OrchestrateOutcome.FAILED,
        final_status=final_status or (run.status if run else "unknown"),
        error_message=error,
    )
