"""Identity context container — UoW + use case providers for the user aggregate.

Cross-cutting dependencies (event_publisher) are declared as
`providers.Dependency` and injected by the root container. This keeps the
sub-container free of imports from sibling containers.

The UoW is a Factory (not Singleton) so each request gets a fresh instance
built with its own per-request session.
"""

from dependency_injector import containers, providers

from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.contexts.identity.adapters.persistence.unit_of_work import (
    SQLAlchemyIdentityUnitOfWork,
)
from src.contexts.identity.use_cases.user.create import CreateUserUseCase
from src.contexts.identity.use_cases.user.delete import DeleteUserUseCase
from src.contexts.identity.use_cases.user.get import GetUserUseCase
from src.contexts.identity.use_cases.user.list import ListUsersUseCase
from src.contexts.identity.use_cases.user.update import UpdateUserUseCase


class IdentityContainer(containers.DeclarativeContainer):
    event_publisher: providers.Dependency[InMemoryEventPublisher] = (
        providers.Dependency()
    )

    identity_uow = providers.Factory(SQLAlchemyIdentityUnitOfWork)

    create_user_use_case = providers.Factory(
        CreateUserUseCase,
        uow=identity_uow,
        event_publisher=event_publisher,
    )
    get_user_use_case = providers.Factory(
        GetUserUseCase,
        uow=identity_uow,
    )
    list_users_use_case = providers.Factory(
        ListUsersUseCase,
        uow=identity_uow,
    )
    update_user_use_case = providers.Factory(
        UpdateUserUseCase,
        uow=identity_uow,
        event_publisher=event_publisher,
    )
    delete_user_use_case = providers.Factory(
        DeleteUserUseCase,
        uow=identity_uow,
        event_publisher=event_publisher,
    )
