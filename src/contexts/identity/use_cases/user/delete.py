"""DeleteUserUseCase — remove a user by id, 404 if absent."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.event_publisher import IEventPublisher
from src.contexts.identity.domain.unit_of_work import IIdentityUnitOfWork
from src.contexts.identity.domain.user.events import UserDeleted


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
        uow: IIdentityUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: DeleteUserRequest) -> DeleteUserResponse:
        async with self._uow:
            deleted = await self._uow.users.delete(request.user_id)
            if not deleted:
                return DeleteUserResponse(False, "User not found.")
            await self._uow.commit()

        await self._publisher.publish([UserDeleted(user_id=request.user_id)])
        return DeleteUserResponse(True)
