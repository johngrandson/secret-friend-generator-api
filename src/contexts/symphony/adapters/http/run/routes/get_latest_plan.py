"""GET /runs/{run_id}/plan — return the latest plan for a run.

Convenience shortcut over ``GET /plans/?run_id=`` returning only the
highest-version plan instead of the full version history.
"""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.plan.deps import (
    ListPlansForRunUseCaseDep,
)
from src.contexts.symphony.adapters.http.plan.serializers import to_plan_output
from src.contexts.symphony.adapters.http.run.router import router
from src.contexts.symphony.use_cases.plan.list_for_run import (
    ListPlansForRunRequest,
)


@router.get("/{run_id}/plan")
async def get_latest_plan_for_run(
    run_id: UUID, list_uc: ListPlansForRunUseCaseDep
) -> dict:
    resp = await list_uc.execute(ListPlansForRunRequest(run_id=run_id))
    if not resp.plans:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="No plan found for this run."
        )
    latest = max(resp.plans, key=lambda p: p.version)
    return to_plan_output(latest)
