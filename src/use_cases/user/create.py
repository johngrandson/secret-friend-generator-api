"""CreateUserUseCase — orchestrates new-user registration."""

from dataclasses import dataclass
from typing import Optional

from src.domain._shared.event_publisher import IEventPublisher
from src.domain.user.email import Email
from src.domain.user.entity import User
from src.domain.user.repository import IUserRepository
from src.use_cases.user.dto import UserDTO


@dataclass
class CreateUserRequest:
    email: str
    name: str


@dataclass
class CreateUserResponse:
    user: Optional[UserDTO]
    success: bool
    error_message: Optional[str] = None


class CreateUserUseCase:
    def __init__(
        self,
        user_repository: IUserRepository,
        event_publisher: IEventPublisher,
    ) -> None:
        self._repo = user_repository
        self._publisher = event_publisher

    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        try:
            email = Email(request.email)
        except ValueError as exc:
            return CreateUserResponse(None, False, str(exc))

        if await self._repo.find_by_email(email):
            return CreateUserResponse(None, False, "Email already registered.")

        try:
            user = User.create(email=email, name=request.name)
        except ValueError as exc:
            return CreateUserResponse(None, False, str(exc))

        saved = await self._repo.save(user)
        events = saved.pull_events()
        if events:
            await self._publisher.publish(events)
        return CreateUserResponse(UserDTO.from_entity(saved), True)
