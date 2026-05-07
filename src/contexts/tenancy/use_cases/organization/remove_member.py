"""RemoveMemberUseCase — remove a user from an organization."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.tenancy.domain.unit_of_work import ITenancyUnitOfWork
from src.contexts.tenancy.use_cases.organization.dto import OrganizationDTO
from src.shared.event_publisher import IEventPublisher


@dataclass
class RemoveMemberRequest:
    organization_id: UUID
    user_id: UUID


@dataclass
class RemoveMemberResponse:
    organization: OrganizationDTO | None
    success: bool
    error_message: str | None = None


class RemoveMemberUseCase:
    def __init__(
        self,
        uow: ITenancyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: RemoveMemberRequest) -> RemoveMemberResponse:
        async with self._uow:
            org = await self._uow.organizations.find_by_id(request.organization_id)
            if org is None:
                return RemoveMemberResponse(None, False, "Organization not found.")

            try:
                org.remove_member(user_id=request.user_id)
            except ValueError as exc:
                return RemoveMemberResponse(None, False, str(exc))

            updated = await self._uow.organizations.update(org)
            await self._uow.commit()
            events = org.pull_events()

        if events:
            await self._publisher.publish(events)
        return RemoveMemberResponse(OrganizationDTO.from_entity(updated), True)
