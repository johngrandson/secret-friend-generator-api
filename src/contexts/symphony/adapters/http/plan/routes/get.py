"""GET /plans/{plan_id} — fetch a single plan by id."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.plan.router import router
from src.contexts.symphony.adapters.http.plan.deps import GetPlanUseCaseDep
from src.contexts.symphony.adapters.http.plan.serializers import to_plan_output
from src.contexts.symphony.use_cases.plan.get import GetPlanRequest


@router.get("/{plan_id}")
async def get_plan(plan_id: UUID, get_uc: GetPlanUseCaseDep) -> dict:
    resp = await get_uc.execute(GetPlanRequest(plan_id=plan_id))
    if not resp.success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
    assert resp.plan is not None
    return to_plan_output(resp.plan)
