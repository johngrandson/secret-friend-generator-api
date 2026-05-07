"""Composite dependency for the Dispatch HTTP route.

Builds :class:`DispatchRunUseCase` with a request-scoped UoW shared with
its embedded :class:`StartRunUseCase`. The dispatch tick uses the
configured backlog adapter and reads ``max_concurrent_agents`` from the
loaded :class:`WorkflowDefinition`.
"""

from collections.abc import Callable
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.contexts.symphony.use_cases.dispatch.dispatch_run import DispatchRunUseCase
from src.contexts.symphony.use_cases.run.start import StartRunUseCase
from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.infrastructure.containers import Container
from src.infrastructure.database import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@inject
def get_dispatch_run_use_case(
    session: SessionDep,
    start_run_factory: Callable[..., StartRunUseCase] = Depends(
        Provide[Container.symphony.start_run_use_case.provider]
    ),
    dispatch_factory: Callable[..., DispatchRunUseCase] = Depends(
        Provide[Container.symphony.dispatch_run_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(
        Provide[Container.core.event_publisher]
    ),
) -> DispatchRunUseCase:
    """Build DispatchRunUseCase + embedded StartRunUseCase sharing one UoW."""
    uow = SQLAlchemySymphonyUnitOfWork(session)
    start_run = start_run_factory(uow=uow, event_publisher=publisher)
    return dispatch_factory(
        uow=uow,
        start_run_use_case=start_run,
        event_publisher=publisher,
    )


DispatchRunUseCaseDep = Annotated[
    DispatchRunUseCase, Depends(get_dispatch_run_use_case)
]
