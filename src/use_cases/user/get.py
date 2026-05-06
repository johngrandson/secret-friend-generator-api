"""GetUserUseCase — fetch a single user by id."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.domain.user.repository import IUserRepository
from src.use_cases.user.dto import UserDTO


@dataclass
class GetUserRequest:
    user_id: UUID


@dataclass
class GetUserResponse:
    user: Optional[UserDTO]
    success: bool
    error_message: Optional[str] = None


class GetUserUseCase:
    def __init__(self, user_repository: IUserRepository) -> None:
        self._repo = user_repository

    async def execute(self, request: GetUserRequest) -> GetUserResponse:
        user = await self._repo.find_by_id(request.user_id)
        if user is None:
            return GetUserResponse(None, False, "User not found.")
        return GetUserResponse(UserDTO.from_entity(user), True)
