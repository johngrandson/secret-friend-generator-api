"""POST /plans/{plan_id}/approve — approve a pending plan version."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.plan.router import router
from src.contexts.symphony.adapters.http.plan.deps import ApprovePlanUseCaseDep
from src.contexts.symphony.adapters.http.plan.schemas import ApprovePlanInput
from src.contexts.symphony.adapters.http.plan.serializers import to_plan_output
from src.contexts.symphony.use_cases.plan.approve import ApprovePlanRequest


@router.post("/{plan_id}/approve")
async def approve_plan(
    plan_id: UUID,
    data: ApprovePlanInput,
    approve_uc: ApprovePlanUseCaseDep,
) -> dict:
    resp = await approve_uc.execute(
        ApprovePlanRequest(plan_id=plan_id, approved_by=data.approved_by)
    )
    if not resp.success:
        if resp.error_message and "not found" in resp.error_message.lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.plan is not None
    return to_plan_output(resp.plan)
