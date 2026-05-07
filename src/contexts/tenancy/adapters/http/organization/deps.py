"""FastAPI dependency helpers for the Organization HTTP layer.

Each get_*_use_case function is decorated with @inject so that
dependency-injector resolves the Provide[Container.tenancy.<uc>.provider] argument.
That gives us a Factory callable. We then call it with a fresh
SQLAlchemyTenancyUnitOfWork built from the per-request session.
Mutation use cases also receive the event_publisher singleton from CoreContainer.
"""

from typing import Annotated
from collections.abc import Callable

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.tenancy.adapters.persistence.unit_of_work import (
    SQLAlchemyTenancyUnitOfWork,
)
from src.contexts.tenancy.use_cases.organization.add_member import AddMemberUseCase
from src.contexts.tenancy.use_cases.organization.change_role import (
    ChangeMemberRoleUseCase,
)
from src.contexts.tenancy.use_cases.organization.create import (
    CreateOrganizationUseCase,
)
from src.contexts.tenancy.use_cases.organization.list_my_organizations import (
    ListMyOrganizationsUseCase,
)
from src.contexts.tenancy.use_cases.organization.remove_member import (
    RemoveMemberUseCase,
)
from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.infrastructure.containers import Container
from src.infrastructure.database import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

core_event_publisher = Provide[Container.core.event_publisher]


@inject
def get_create_organization_use_case(
    session: SessionDep,
    factory: Callable[..., CreateOrganizationUseCase] = Depends(
        Provide[Container.tenancy.create_organization_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> CreateOrganizationUseCase:
    return factory(
        uow=SQLAlchemyTenancyUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_add_member_use_case(
    session: SessionDep,
    factory: Callable[..., AddMemberUseCase] = Depends(
        Provide[Container.tenancy.add_member_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> AddMemberUseCase:
    return factory(
        uow=SQLAlchemyTenancyUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_remove_member_use_case(
    session: SessionDep,
    factory: Callable[..., RemoveMemberUseCase] = Depends(
        Provide[Container.tenancy.remove_member_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> RemoveMemberUseCase:
    return factory(
        uow=SQLAlchemyTenancyUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_change_member_role_use_case(
    session: SessionDep,
    factory: Callable[..., ChangeMemberRoleUseCase] = Depends(
        Provide[Container.tenancy.change_member_role_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> ChangeMemberRoleUseCase:
    return factory(
        uow=SQLAlchemyTenancyUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_list_my_organizations_use_case(
    session: SessionDep,
    factory: Callable[..., ListMyOrganizationsUseCase] = Depends(
        Provide[Container.tenancy.list_my_organizations_use_case.provider]
    ),
) -> ListMyOrganizationsUseCase:
    return factory(uow=SQLAlchemyTenancyUnitOfWork(session))


CreateOrganizationUseCaseDep = Annotated[
    CreateOrganizationUseCase, Depends(get_create_organization_use_case)
]
AddMemberUseCaseDep = Annotated[AddMemberUseCase, Depends(get_add_member_use_case)]
RemoveMemberUseCaseDep = Annotated[
    RemoveMemberUseCase, Depends(get_remove_member_use_case)
]
ChangeMemberRoleUseCaseDep = Annotated[
    ChangeMemberRoleUseCase, Depends(get_change_member_role_use_case)
]
ListMyOrganizationsUseCaseDep = Annotated[
    ListMyOrganizationsUseCase, Depends(get_list_my_organizations_use_case)
]
