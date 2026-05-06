"""UpdateUserUseCase — change name and/or active status of an existing user."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.event_publisher import IEventPublisher
from src.contexts.identity.domain.unit_of_work import IIdentityUnitOfWork
from src.contexts.identity.use_cases.user.dto import UserDTO


@dataclass
class UpdateUserRequest:
    user_id: UUID
    name: str | None = None
    is_active: bool | None = None


@dataclass
class UpdateUserResponse:
    user: UserDTO | None
    success: bool
    error_message: str | None = None


class UpdateUserUseCase:
    def __init__(
        self,
        uow: IIdentityUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: UpdateUserRequest) -> UpdateUserResponse:
        async with self._uow:
            user = await self._uow.users.find_by_id(request.user_id)
            if user is None:
                return UpdateUserResponse(None, False, "User not found.")

            try:
                if request.name is not None:
                    user.update_name(request.name)
                if request.is_active is not None:
                    if request.is_active:
                        user.activate()
                    else:
                        user.deactivate()
            except ValueError as exc:
                return UpdateUserResponse(None, False, str(exc))

            updated = await self._uow.users.update(user)
            await self._uow.commit()
            events = user.pull_events()

        if events:  # pragma: no branch
            await self._publisher.publish(events)
        return UpdateUserResponse(UserDTO.from_entity(updated), True)
