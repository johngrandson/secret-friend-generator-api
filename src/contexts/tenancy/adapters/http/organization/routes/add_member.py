"""POST /organizations/{org_id}/members — add a member to an organization."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.tenancy.adapters.http.organization.deps import (
    AddMemberUseCaseDep,
)
from src.contexts.tenancy.adapters.http.organization.router import router
from src.contexts.tenancy.adapters.http.organization.schemas import AddMemberInput
from src.contexts.tenancy.adapters.http.organization.serializers import (
    to_organization_output,
)
from src.contexts.tenancy.use_cases.organization.add_member import AddMemberRequest


@router.post("/{org_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    org_id: UUID,
    data: AddMemberInput,
    add_uc: AddMemberUseCaseDep,
) -> dict:
    resp = await add_uc.execute(
        AddMemberRequest(
            organization_id=org_id, user_id=data.user_id, role=data.role
        )
    )
    if not resp.success:
        if resp.error_message == "Organization not found.":
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.organization is not None
    return to_organization_output(resp.organization)
