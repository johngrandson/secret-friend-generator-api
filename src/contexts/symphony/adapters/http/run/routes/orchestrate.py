"""POST /runs/{run_id}/orchestrate — drive one orchestration tick.

Builds an :class:`OrchestrationContext` from the loaded
:class:`WorkflowDefinition` + the issue resolved via the configured
backlog adapter, then runs ``OrchestrateRunUseCase.execute`` once. The
caller (operator UI, manual trigger) re-invokes after approval gates
or retry windows.
"""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.run.orchestration_dep import (
    BacklogAdapterDep,
    OrchestrateRunUseCaseDep,
    WorkflowDefinitionDep,
)
from src.contexts.symphony.adapters.http.run.router import router
from src.contexts.symphony.adapters.http.run.serializers import (
    to_orchestrate_run_output,
)
from src.contexts.symphony.use_cases.orchestration.orchestrate_run import (
    OrchestrateRunRequest,
    OrchestrationContext,
)


@router.post("/{run_id}/orchestrate")
async def orchestrate_run(
    run_id: UUID,
    use_case: OrchestrateRunUseCaseDep,
    backlog: BacklogAdapterDep,
    workflow: WorkflowDefinitionDep,
) -> dict:
    """Drive the symphony pipeline forward by one tick for ``run_id``."""
    issues = await backlog.fetch_active_issues()
    issue = next(
        (i for i in issues if str(i.identifier) == str(run_id)), None
    )
    # Run.issue_id may be the issue identifier (string), not the run UUID; try
    # again resolving by issue_id stored on the run.
    if issue is None:
        # Best effort: pick any issue whose identifier appears under the run.
        # The orchestrate context requires an Issue; if backlog cannot supply
        # one, surface a 422 rather than crashing inside the use case.
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No active backlog issue maps to this run; orchestration needs "
                "an Issue payload (try POST /runs/dispatch instead, which "
                "starts new runs from the backlog)."
            ),
        )

    cfg = workflow.config
    context = OrchestrationContext(
        issue=issue,
        execute_prompt_template=workflow.prompt_template,
        model_name=cfg.claude_code.api_model,
        harness_config=cfg.harness,
        pr_branch=f"symphony/{issue.identifier}",
        pr_base_branch=cfg.pr.base_branch,
        pr_title=f"[{issue.identifier}] {issue.title}",
        pr_is_draft=cfg.pr.draft,
        pr_labels=tuple(cfg.pr.labels),
    )
    response = await use_case.execute(
        OrchestrateRunRequest(run_id=run_id, context=context)
    )
    return to_orchestrate_run_output(response)
