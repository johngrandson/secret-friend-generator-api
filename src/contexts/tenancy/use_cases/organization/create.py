"""CreateOrganizationUseCase — orchestrates new organization creation."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.value_objects import Slug
from src.contexts.tenancy.domain.unit_of_work import ITenancyUnitOfWork
from src.contexts.tenancy.use_cases.organization.dto import OrganizationDTO
from src.shared.event_publisher import IEventPublisher


@dataclass
class CreateOrganizationRequest:
    name: str
    slug: str
    owner_user_id: UUID


@dataclass
class CreateOrganizationResponse:
    organization: OrganizationDTO | None
    success: bool
    error_message: str | None = None


class CreateOrganizationUseCase:
    def __init__(
        self,
        uow: ITenancyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(
        self, request: CreateOrganizationRequest
    ) -> CreateOrganizationResponse:
        try:
            slug = Slug(request.slug)
        except ValueError as exc:
            return CreateOrganizationResponse(None, False, str(exc))

        async with self._uow:
            if await self._uow.organizations.find_by_slug(slug):
                return CreateOrganizationResponse(
                    None, False, "Slug already taken."
                )
            try:
                org = Organization.create(
                    name=request.name,
                    slug=slug,
                    owner_user_id=request.owner_user_id,
                )
            except ValueError as exc:
                return CreateOrganizationResponse(None, False, str(exc))

            saved = await self._uow.organizations.save(org)
            await self._uow.commit()
            events = org.pull_events()

        if events:
            await self._publisher.publish(events)
        return CreateOrganizationResponse(OrganizationDTO.from_entity(saved), True)
