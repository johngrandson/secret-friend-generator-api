"""GET /organizations/?user_id={id} — list organizations for a user."""

from uuid import UUID

from src.contexts.tenancy.adapters.http.organization.deps import (
    ListMyOrganizationsUseCaseDep,
)
from src.contexts.tenancy.adapters.http.organization.router import router
from src.contexts.tenancy.adapters.http.organization.serializers import (
    to_organization_output,
)
from src.contexts.tenancy.use_cases.organization.list_my_organizations import (
    ListMyOrganizationsRequest,
)


@router.get("/")
async def list_my_organizations(
    user_id: UUID,
    list_uc: ListMyOrganizationsUseCaseDep,
) -> dict:
    resp = await list_uc.execute(ListMyOrganizationsRequest(user_id=user_id))
    return {
        "organizations": [to_organization_output(o) for o in resp.organizations],
    }
