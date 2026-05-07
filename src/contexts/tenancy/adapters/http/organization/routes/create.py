"""POST /organizations/ — create a new organization."""

from fastapi import HTTPException, status

from src.contexts.tenancy.adapters.http.organization.deps import (
    CreateOrganizationUseCaseDep,
)
from src.contexts.tenancy.adapters.http.organization.router import router
from src.contexts.tenancy.adapters.http.organization.schemas import (
    CreateOrganizationInput,
)
from src.contexts.tenancy.adapters.http.organization.serializers import (
    to_organization_output,
)
from src.contexts.tenancy.use_cases.organization.create import (
    CreateOrganizationRequest,
)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: CreateOrganizationInput,
    create_uc: CreateOrganizationUseCaseDep,
) -> dict:
    resp = await create_uc.execute(
        CreateOrganizationRequest(
            name=data.name,
            slug=data.slug,
            owner_user_id=data.owner_user_id,
        )
    )
    if not resp.success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.organization is not None
    return to_organization_output(resp.organization)
