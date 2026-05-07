"""PATCH /organizations/{org_id}/members/{user_id} — change a member's role."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.tenancy.adapters.http.organization.deps import (
    ChangeMemberRoleUseCaseDep,
)
from src.contexts.tenancy.adapters.http.organization.router import router
from src.contexts.tenancy.adapters.http.organization.schemas import (
    ChangeMemberRoleInput,
)
from src.contexts.tenancy.adapters.http.organization.serializers import (
    to_organization_output,
)
from src.contexts.tenancy.use_cases.organization.change_role import (
    ChangeMemberRoleRequest,
)


@router.patch("/{org_id}/members/{user_id}")
async def change_member_role(
    org_id: UUID,
    user_id: UUID,
    data: ChangeMemberRoleInput,
    change_uc: ChangeMemberRoleUseCaseDep,
) -> dict:
    resp = await change_uc.execute(
        ChangeMemberRoleRequest(
            organization_id=org_id, user_id=user_id, new_role=data.role
        )
    )
    if not resp.success:
        if resp.error_message == "Organization not found.":
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.organization is not None
    return to_organization_output(resp.organization)
