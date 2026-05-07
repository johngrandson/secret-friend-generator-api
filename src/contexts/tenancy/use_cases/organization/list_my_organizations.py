"""ListMyOrganizationsUseCase — query organizations a user belongs to."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.tenancy.domain.unit_of_work import ITenancyUnitOfWork
from src.contexts.tenancy.use_cases.organization.dto import OrganizationDTO


@dataclass
class ListMyOrganizationsRequest:
    user_id: UUID


@dataclass
class ListMyOrganizationsResponse:
    organizations: tuple[OrganizationDTO, ...]


class ListMyOrganizationsUseCase:
    def __init__(self, uow: ITenancyUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, request: ListMyOrganizationsRequest
    ) -> ListMyOrganizationsResponse:
        async with self._uow:
            orgs = await self._uow.organizations.list_for_user(request.user_id)
        return ListMyOrganizationsResponse(
            organizations=tuple(OrganizationDTO.from_entity(o) for o in orgs)
        )
