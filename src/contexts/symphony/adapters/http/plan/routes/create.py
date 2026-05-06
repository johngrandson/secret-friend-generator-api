"""POST /plans/ — create a new plan version for a run."""

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.plan.router import router
from src.contexts.symphony.adapters.http.plan.deps import CreatePlanUseCaseDep
from src.contexts.symphony.adapters.http.plan.schemas import CreatePlanInput
from src.contexts.symphony.adapters.http.plan.serializers import to_plan_output
from src.contexts.symphony.use_cases.plan.create import CreatePlanRequest


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: CreatePlanInput,
    create_uc: CreatePlanUseCaseDep,
) -> dict:
    resp = await create_uc.execute(
        CreatePlanRequest(
            run_id=data.run_id,
            version=data.version,
            content=data.content,
        )
    )
    if not resp.success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.plan is not None
    return to_plan_output(resp.plan)
