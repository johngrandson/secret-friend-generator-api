"""POST /runs/dispatch — drive one dispatch tick.

Manual trigger for the same ``DispatchRunUseCase`` Celery beat will run
periodically once F08 wiring lands. Useful for dev / smoke testing the
full pipeline without waiting for the scheduler.
"""

from src.contexts.symphony.adapters.http.run.dispatch_dep import (
    DispatchRunUseCaseDep,
)
from src.contexts.symphony.adapters.http.run.orchestration_dep import (
    BacklogAdapterDep,
    WorkflowDefinitionDep,
)
from src.contexts.symphony.adapters.http.run.router import router
from src.contexts.symphony.use_cases.dispatch.dispatch_run import DispatchRunRequest


@router.post("/dispatch")
async def dispatch_run(
    use_case: DispatchRunUseCaseDep,
    backlog: BacklogAdapterDep,
    workflow: WorkflowDefinitionDep,
) -> dict:
    """Run one dispatch tick: pick highest-priority work and start a run."""
    response = await use_case.execute(
        DispatchRunRequest(
            backlog=backlog,
            max_concurrent=workflow.config.agent.max_concurrent_agents,
        )
    )
    return {
        "outcome": response.outcome.value,
        "run_id": str(response.run_id) if response.run_id else None,
        "issue_identifier": response.issue_identifier,
    }
