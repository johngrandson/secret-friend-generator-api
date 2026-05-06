"""FastAPI dependency helpers for the User HTTP layer.

Each get_*_use_case function is decorated with @inject so that
dependency-injector resolves the Provide[Container.identity.<uc>.provider] argument.
That gives us a Factory callable. We then call it with a fresh
SQLAlchemyIdentityUnitOfWork built from the per-request session.
Mutation use cases also receive the event_publisher singleton from CoreContainer.
"""

from typing import Annotated
from collections.abc import Callable

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.contexts.identity.adapters.persistence.unit_of_work import (
    SQLAlchemyIdentityUnitOfWork,
)
from src.infrastructure.containers import Container
from src.infrastructure.database import get_session
from src.contexts.identity.use_cases.user.create import CreateUserUseCase
from src.contexts.identity.use_cases.user.delete import DeleteUserUseCase
from src.contexts.identity.use_cases.user.get import GetUserUseCase
from src.contexts.identity.use_cases.user.list import ListUsersUseCase
from src.contexts.identity.use_cases.user.update import UpdateUserUseCase

SessionDep = Annotated[AsyncSession, Depends(get_session)]

core_event_publisher = Provide[Container.core.event_publisher]


@inject
def get_create_user_use_case(
    session: SessionDep,
    factory: Callable[..., CreateUserUseCase] = Depends(
        Provide[Container.identity.create_user_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> CreateUserUseCase:
    return factory(
        uow=SQLAlchemyIdentityUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_get_user_use_case(
    session: SessionDep,
    factory: Callable[..., GetUserUseCase] = Depends(
        Provide[Container.identity.get_user_use_case.provider]
    ),
) -> GetUserUseCase:
    return factory(uow=SQLAlchemyIdentityUnitOfWork(session))


@inject
def get_list_users_use_case(
    session: SessionDep,
    factory: Callable[..., ListUsersUseCase] = Depends(
        Provide[Container.identity.list_users_use_case.provider]
    ),
) -> ListUsersUseCase:
    return factory(uow=SQLAlchemyIdentityUnitOfWork(session))


@inject
def get_update_user_use_case(
    session: SessionDep,
    factory: Callable[..., UpdateUserUseCase] = Depends(
        Provide[Container.identity.update_user_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> UpdateUserUseCase:
    return factory(
        uow=SQLAlchemyIdentityUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_delete_user_use_case(
    session: SessionDep,
    factory: Callable[..., DeleteUserUseCase] = Depends(
        Provide[Container.identity.delete_user_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> DeleteUserUseCase:
    return factory(
        uow=SQLAlchemyIdentityUnitOfWork(session),
        event_publisher=publisher,
    )


CreateUserUseCaseDep = Annotated[CreateUserUseCase, Depends(get_create_user_use_case)]
GetUserUseCaseDep = Annotated[GetUserUseCase, Depends(get_get_user_use_case)]
ListUsersUseCaseDep = Annotated[ListUsersUseCase, Depends(get_list_users_use_case)]
UpdateUserUseCaseDep = Annotated[UpdateUserUseCase, Depends(get_update_user_use_case)]
DeleteUserUseCaseDep = Annotated[DeleteUserUseCase, Depends(get_delete_user_use_case)]
