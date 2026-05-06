"""POST /specs/{spec_id}/approve — approve a pending spec version."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.spec.router import router
from src.contexts.symphony.adapters.http.spec.deps import ApproveSpecUseCaseDep
from src.contexts.symphony.adapters.http.spec.schemas import ApproveSpecInput
from src.contexts.symphony.adapters.http.spec.serializers import to_spec_output
from src.contexts.symphony.use_cases.spec.approve import ApproveSpecRequest


@router.post("/{spec_id}/approve")
async def approve_spec(
    spec_id: UUID,
    data: ApproveSpecInput,
    approve_uc: ApproveSpecUseCaseDep,
) -> dict:
    resp = await approve_uc.execute(
        ApproveSpecRequest(spec_id=spec_id, approved_by=data.approved_by)
    )
    if not resp.success:
        if resp.error_message and "not found" in resp.error_message.lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.spec is not None
    return to_spec_output(resp.spec)
