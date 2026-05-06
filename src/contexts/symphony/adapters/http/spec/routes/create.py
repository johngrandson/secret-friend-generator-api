"""POST /specs/ — create a new spec version for a run."""

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.spec.router import router
from src.contexts.symphony.adapters.http.spec.deps import CreateSpecUseCaseDep
from src.contexts.symphony.adapters.http.spec.schemas import CreateSpecInput
from src.contexts.symphony.adapters.http.spec.serializers import to_spec_output
from src.contexts.symphony.use_cases.spec.create import CreateSpecRequest


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_spec(
    data: CreateSpecInput,
    create_uc: CreateSpecUseCaseDep,
) -> dict:
    resp = await create_uc.execute(
        CreateSpecRequest(
            run_id=data.run_id,
            version=data.version,
            content=data.content,
        )
    )
    if not resp.success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.spec is not None
    return to_spec_output(resp.spec)
