"""UpdateUserUseCase — change name and/or active status of an existing user."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.domain._shared.event_publisher import IEventPublisher
from src.domain.user.repository import IUserRepository
from src.use_cases.user.dto import UserDTO


@dataclass
class UpdateUserRequest:
    user_id: UUID
    name: Optional[str] = None
    is_active: Optional[bool] = None


@dataclass
class UpdateUserResponse:
    user: Optional[UserDTO]
    success: bool
    error_message: Optional[str] = None


class UpdateUserUseCase:
    def __init__(
        self,
        user_repository: IUserRepository,
        event_publisher: IEventPublisher,
    ) -> None:
        self._repo = user_repository
        self._publisher = event_publisher

    async def execute(self, request: UpdateUserRequest) -> UpdateUserResponse:
        user = await self._repo.find_by_id(request.user_id)
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

        updated = await self._repo.update(user)
        events = updated.pull_events()
        if events:
            await self._publisher.publish(events)
        return UpdateUserResponse(UserDTO.from_entity(updated), True)
