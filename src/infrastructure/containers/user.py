"""User aggregate container — repository + use case providers.

Cross-cutting dependencies (event_publisher) are declared as
`providers.Dependency` and injected by the root container. This keeps the
sub-container free of imports from sibling containers.
"""

from dependency_injector import containers, providers

from src.adapters.events.in_memory_publisher import InMemoryEventPublisher
from src.adapters.persistence.user.repository import SQLAlchemyUserRepository
from src.use_cases.user.create import CreateUserUseCase
from src.use_cases.user.delete import DeleteUserUseCase
from src.use_cases.user.get import GetUserUseCase
from src.use_cases.user.list import ListUsersUseCase
from src.use_cases.user.update import UpdateUserUseCase


class UserContainer(containers.DeclarativeContainer):
    event_publisher: providers.Dependency[InMemoryEventPublisher] = (
        providers.Dependency()
    )

    user_repository = providers.Factory(SQLAlchemyUserRepository)

    create_user_use_case = providers.Factory(
        CreateUserUseCase,
        user_repository=user_repository,
        event_publisher=event_publisher,
    )
    get_user_use_case = providers.Factory(
        GetUserUseCase,
        user_repository=user_repository,
    )
    list_users_use_case = providers.Factory(
        ListUsersUseCase,
        user_repository=user_repository,
    )
    update_user_use_case = providers.Factory(
        UpdateUserUseCase,
        user_repository=user_repository,
        event_publisher=event_publisher,
    )
    delete_user_use_case = providers.Factory(
        DeleteUserUseCase,
        user_repository=user_repository,
        event_publisher=event_publisher,
    )
