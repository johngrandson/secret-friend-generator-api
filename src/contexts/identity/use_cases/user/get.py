"""GetUserUseCase — fetch a single user by id."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.identity.domain.unit_of_work import IIdentityUnitOfWork
from src.contexts.identity.use_cases.user.dto import UserDTO


@dataclass
class GetUserRequest:
    user_id: UUID


@dataclass
class GetUserResponse:
    user: UserDTO | None
    success: bool
    error_message: str | None = None


class GetUserUseCase:
    def __init__(self, uow: IIdentityUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, request: GetUserRequest) -> GetUserResponse:
        async with self._uow:
            user = await self._uow.users.find_by_id(request.user_id)
        if user is None:
            return GetUserResponse(None, False, "User not found.")
        return GetUserResponse(UserDTO.from_entity(user), True)
