"""ChangeMemberRoleUseCase — change an existing member's role."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.tenancy.domain.role.value_objects import Role
from src.contexts.tenancy.domain.unit_of_work import ITenancyUnitOfWork
from src.contexts.tenancy.use_cases.organization.dto import OrganizationDTO
from src.shared.event_publisher import IEventPublisher


@dataclass
class ChangeMemberRoleRequest:
    organization_id: UUID
    user_id: UUID
    new_role: Role


@dataclass
class ChangeMemberRoleResponse:
    organization: OrganizationDTO | None
    success: bool
    error_message: str | None = None


class ChangeMemberRoleUseCase:
    def __init__(
        self,
        uow: ITenancyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(
        self, request: ChangeMemberRoleRequest
    ) -> ChangeMemberRoleResponse:
        async with self._uow:
            org = await self._uow.organizations.find_by_id(request.organization_id)
            if org is None:
                return ChangeMemberRoleResponse(None, False, "Organization not found.")

            try:
                org.change_member_role(
                    user_id=request.user_id, new_role=request.new_role
                )
            except ValueError as exc:
                return ChangeMemberRoleResponse(None, False, str(exc))

            updated = await self._uow.organizations.update(org)
            await self._uow.commit()
            events = org.pull_events()

        if events:
            await self._publisher.publish(events)
        return ChangeMemberRoleResponse(OrganizationDTO.from_entity(updated), True)
