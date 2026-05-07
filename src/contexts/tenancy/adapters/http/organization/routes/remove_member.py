"""DELETE /organizations/{org_id}/members/{user_id} — remove a member."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.tenancy.adapters.http.organization.deps import (
    RemoveMemberUseCaseDep,
)
from src.contexts.tenancy.adapters.http.organization.router import router
from src.contexts.tenancy.adapters.http.organization.serializers import (
    to_organization_output,
)
from src.contexts.tenancy.use_cases.organization.remove_member import (
    RemoveMemberRequest,
)


@router.delete("/{org_id}/members/{user_id}")
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    remove_uc: RemoveMemberUseCaseDep,
) -> dict:
    resp = await remove_uc.execute(
        RemoveMemberRequest(organization_id=org_id, user_id=user_id)
    )
    if not resp.success:
        if resp.error_message == "Organization not found.":
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.organization is not None
    return to_organization_output(resp.organization)
