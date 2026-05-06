"""POST /plans/{plan_id}/reject — reject a pending plan version."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.plan.router import router
from src.contexts.symphony.adapters.http.plan.deps import RejectPlanUseCaseDep
from src.contexts.symphony.adapters.http.plan.schemas import RejectPlanInput
from src.contexts.symphony.adapters.http.plan.serializers import to_plan_output
from src.contexts.symphony.use_cases.plan.reject import RejectPlanRequest


@router.post("/{plan_id}/reject")
async def reject_plan(
    plan_id: UUID,
    data: RejectPlanInput,
    reject_uc: RejectPlanUseCaseDep,
) -> dict:
    resp = await reject_uc.execute(
        RejectPlanRequest(plan_id=plan_id, reason=data.reason)
    )
    if not resp.success:
        if resp.error_message and "not found" in resp.error_message.lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.plan is not None
    return to_plan_output(resp.plan)
