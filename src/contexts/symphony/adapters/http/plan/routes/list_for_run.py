"""GET /plans/ — list all plan versions for a given run."""

from uuid import UUID

from fastapi import Query

from src.contexts.symphony.adapters.http.plan.router import router
from src.contexts.symphony.adapters.http.plan.deps import ListPlansForRunUseCaseDep
from src.contexts.symphony.adapters.http.plan.serializers import to_plan_output
from src.contexts.symphony.use_cases.plan.list_for_run import ListPlansForRunRequest


@router.get("/")
async def list_plans_for_run(
    list_uc: ListPlansForRunUseCaseDep,
    run_id: UUID = Query(...),
) -> list:
    resp = await list_uc.execute(ListPlansForRunRequest(run_id=run_id))
    return [to_plan_output(p) for p in resp.plans]
