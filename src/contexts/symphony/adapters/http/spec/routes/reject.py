"""POST /specs/{spec_id}/reject — reject a pending spec version."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.spec.router import router
from src.contexts.symphony.adapters.http.spec.deps import RejectSpecUseCaseDep
from src.contexts.symphony.adapters.http.spec.schemas import RejectSpecInput
from src.contexts.symphony.adapters.http.spec.serializers import to_spec_output
from src.contexts.symphony.use_cases.spec.reject import RejectSpecRequest


@router.post("/{spec_id}/reject")
async def reject_spec(
    spec_id: UUID,
    data: RejectSpecInput,
    reject_uc: RejectSpecUseCaseDep,
) -> dict:
    resp = await reject_uc.execute(
        RejectSpecRequest(spec_id=spec_id, reason=data.reason)
    )
    if not resp.success:
        if resp.error_message and "not found" in resp.error_message.lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.spec is not None
    return to_spec_output(resp.spec)
