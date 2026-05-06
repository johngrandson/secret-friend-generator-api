"""FastAPI dependency helpers for the Spec HTTP layer.

Each get_*_use_case function is decorated with @inject so that
dependency-injector resolves the Provide[Container.symphony.<uc>.provider] argument.
That gives us a Factory callable. We then call it with a fresh
SQLAlchemySymphonyUnitOfWork built from the per-request session.
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
from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.infrastructure.containers import Container
from src.infrastructure.database import get_session
from src.contexts.symphony.use_cases.spec.create import CreateSpecUseCase
from src.contexts.symphony.use_cases.spec.get import GetSpecUseCase
from src.contexts.symphony.use_cases.spec.list_for_run import ListSpecsForRunUseCase
from src.contexts.symphony.use_cases.spec.approve import ApproveSpecUseCase
from src.contexts.symphony.use_cases.spec.reject import RejectSpecUseCase

SessionDep = Annotated[AsyncSession, Depends(get_session)]

core_event_publisher = Provide[Container.core.event_publisher]


@inject
def get_create_spec_use_case(
    session: SessionDep,
    factory: Callable[..., CreateSpecUseCase] = Depends(
        Provide[Container.symphony.create_spec_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> CreateSpecUseCase:
    return factory(
        uow=SQLAlchemySymphonyUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_get_spec_use_case(
    session: SessionDep,
    factory: Callable[..., GetSpecUseCase] = Depends(
        Provide[Container.symphony.get_spec_use_case.provider]
    ),
) -> GetSpecUseCase:
    return factory(uow=SQLAlchemySymphonyUnitOfWork(session))


@inject
def get_list_specs_for_run_use_case(
    session: SessionDep,
    factory: Callable[..., ListSpecsForRunUseCase] = Depends(
        Provide[Container.symphony.list_specs_for_run_use_case.provider]
    ),
) -> ListSpecsForRunUseCase:
    return factory(uow=SQLAlchemySymphonyUnitOfWork(session))


@inject
def get_approve_spec_use_case(
    session: SessionDep,
    factory: Callable[..., ApproveSpecUseCase] = Depends(
        Provide[Container.symphony.approve_spec_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> ApproveSpecUseCase:
    return factory(
        uow=SQLAlchemySymphonyUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_reject_spec_use_case(
    session: SessionDep,
    factory: Callable[..., RejectSpecUseCase] = Depends(
        Provide[Container.symphony.reject_spec_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> RejectSpecUseCase:
    return factory(
        uow=SQLAlchemySymphonyUnitOfWork(session),
        event_publisher=publisher,
    )


CreateSpecUseCaseDep = Annotated[CreateSpecUseCase, Depends(get_create_spec_use_case)]
GetSpecUseCaseDep = Annotated[GetSpecUseCase, Depends(get_get_spec_use_case)]
ListSpecsForRunUseCaseDep = Annotated[
    ListSpecsForRunUseCase, Depends(get_list_specs_for_run_use_case)
]
ApproveSpecUseCaseDep = Annotated[
    ApproveSpecUseCase, Depends(get_approve_spec_use_case)
]
RejectSpecUseCaseDep = Annotated[RejectSpecUseCase, Depends(get_reject_spec_use_case)]
