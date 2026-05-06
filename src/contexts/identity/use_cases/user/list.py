"""ListUsersUseCase — return a paginated list of users."""

from dataclasses import dataclass, field

from src.contexts.identity.domain.unit_of_work import IIdentityUnitOfWork
from src.contexts.identity.use_cases.user.dto import UserDTO


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
    def __init__(self, uow: IIdentityUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, request: ListUsersRequest) -> ListUsersResponse:
        async with self._uow:
            users = await self._uow.users.list(
                limit=request.limit, offset=request.offset
            )
        return ListUsersResponse(users=[UserDTO.from_entity(u) for u in users])
