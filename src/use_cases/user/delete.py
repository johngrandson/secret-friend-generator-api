"""DeleteUserUseCase — remove a user by id, 404 if absent."""

from dataclasses import dataclass
from uuid import UUID

from src.domain._shared.event_publisher import IEventPublisher
from src.domain.user.repository import IUserRepository
from src.domain.user.events import UserDeleted


@dataclass
class DeleteUserRequest:
    user_id: UUID


@dataclass
class DeleteUserResponse:
    success: bool
    error_message: str | None = None


class DeleteUserUseCase:
    def __init__(
        self,
        user_repository: IUserRepository,
        event_publisher: IEventPublisher,
    ) -> None:
        self._repo = user_repository
        self._publisher = event_publisher

    async def execute(self, request: DeleteUserRequest) -> DeleteUserResponse:
        deleted = await self._repo.delete(request.user_id)
        if not deleted:
            return DeleteUserResponse(False, "User not found.")
        await self._publisher.publish([UserDeleted(user_id=request.user_id)])
        return DeleteUserResponse(True)
