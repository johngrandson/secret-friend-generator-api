"""ListUsersUseCase — return a paginated list of users."""

from dataclasses import dataclass, field

from src.domain.user.repository import IUserRepository
from src.use_cases.user.dto import UserDTO


@dataclass
class ListUsersRequest:
    limit: int = 20
    offset: int = 0


@dataclass
class ListUsersResponse:
    users: list[UserDTO] = field(default_factory=list)
    success: bool = True
    error_message: str | None = None


class ListUsersUseCase:
    def __init__(self, user_repository: IUserRepository) -> None:
        self._repo = user_repository

    async def execute(self, request: ListUsersRequest) -> ListUsersResponse:
        users = await self._repo.list(limit=request.limit, offset=request.offset)
        return ListUsersResponse(users=[UserDTO.from_entity(u) for u in users])
