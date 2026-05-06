"""CreateUserUseCase — orchestrates new-user registration."""

from dataclasses import dataclass

from src.shared.event_publisher import IEventPublisher
from src.contexts.identity.domain.unit_of_work import IIdentityUnitOfWork
from src.contexts.identity.domain.user.email import Email
from src.contexts.identity.domain.user.entity import User
from src.contexts.identity.use_cases.user.dto import UserDTO


@dataclass
class CreateUserRequest:
    email: str
    name: str


@dataclass
class CreateUserResponse:
    user: UserDTO | None
    success: bool
    error_message: str | None = None


class CreateUserUseCase:
    def __init__(
        self,
        uow: IIdentityUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        try:
            email = Email(request.email)
        except ValueError as exc:
            return CreateUserResponse(None, False, str(exc))

        async with self._uow:
            if await self._uow.users.find_by_email(email):
                return CreateUserResponse(None, False, "Email already registered.")

            try:
                user = User.create(email=email, name=request.name)
            except ValueError as exc:
                return CreateUserResponse(None, False, str(exc))

            saved = await self._uow.users.save(user)
            await self._uow.commit()
            events = user.pull_events()

        if events:  # pragma: no branch
            await self._publisher.publish(events)
        return CreateUserResponse(UserDTO.from_entity(saved), True)
