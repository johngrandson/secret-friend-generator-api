"""POST /runs/ — create a new pipeline run."""

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.run.router import router
from src.contexts.symphony.adapters.http.run.deps import CreateRunUseCaseDep
from src.contexts.symphony.adapters.http.run.schemas import CreateRunInput
from src.contexts.symphony.adapters.http.run.serializers import to_run_output
from src.contexts.symphony.use_cases.run.create import CreateRunRequest


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_run(
    data: CreateRunInput,
    create_uc: CreateRunUseCaseDep,
) -> dict:
    resp = await create_uc.execute(CreateRunRequest(issue_id=data.issue_id))
    if not resp.success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.run is not None
    return to_run_output(resp.run)
