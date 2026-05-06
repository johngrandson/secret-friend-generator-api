"""FastAPI dependency helpers for the Run HTTP layer.

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
from src.contexts.symphony.use_cases.run.create import CreateRunUseCase
from src.contexts.symphony.use_cases.run.get import GetRunUseCase
from src.contexts.symphony.use_cases.run.list import ListRunsUseCase

SessionDep = Annotated[AsyncSession, Depends(get_session)]

core_event_publisher = Provide[Container.core.event_publisher]


@inject
def get_create_run_use_case(
    session: SessionDep,
    factory: Callable[..., CreateRunUseCase] = Depends(
        Provide[Container.symphony.create_run_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> CreateRunUseCase:
    return factory(
        uow=SQLAlchemySymphonyUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_get_run_use_case(
    session: SessionDep,
    factory: Callable[..., GetRunUseCase] = Depends(
        Provide[Container.symphony.get_run_use_case.provider]
    ),
) -> GetRunUseCase:
    return factory(uow=SQLAlchemySymphonyUnitOfWork(session))


@inject
def get_list_runs_use_case(
    session: SessionDep,
    factory: Callable[..., ListRunsUseCase] = Depends(
        Provide[Container.symphony.list_runs_use_case.provider]
    ),
) -> ListRunsUseCase:
    return factory(uow=SQLAlchemySymphonyUnitOfWork(session))


CreateRunUseCaseDep = Annotated[CreateRunUseCase, Depends(get_create_run_use_case)]
GetRunUseCaseDep = Annotated[GetRunUseCase, Depends(get_get_run_use_case)]
ListRunsUseCaseDep = Annotated[ListRunsUseCase, Depends(get_list_runs_use_case)]
