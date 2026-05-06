"""GET /specs/{spec_id} — fetch a single spec by id."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.spec.router import router
from src.contexts.symphony.adapters.http.spec.deps import GetSpecUseCaseDep
from src.contexts.symphony.adapters.http.spec.serializers import to_spec_output
from src.contexts.symphony.use_cases.spec.get import GetSpecRequest


@router.get("/{spec_id}")
async def get_spec(spec_id: UUID, get_uc: GetSpecUseCaseDep) -> dict:
    resp = await get_uc.execute(GetSpecRequest(spec_id=spec_id))
    if not resp.success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
    assert resp.spec is not None
    return to_spec_output(resp.spec)
