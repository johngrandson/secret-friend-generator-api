"""FastAPI dependency helpers for the Plan HTTP layer.

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
from src.contexts.symphony.use_cases.plan.create import CreatePlanUseCase
from src.contexts.symphony.use_cases.plan.get import GetPlanUseCase
from src.contexts.symphony.use_cases.plan.list_for_run import ListPlansForRunUseCase
from src.contexts.symphony.use_cases.plan.approve import ApprovePlanUseCase
from src.contexts.symphony.use_cases.plan.reject import RejectPlanUseCase

SessionDep = Annotated[AsyncSession, Depends(get_session)]

core_event_publisher = Provide[Container.core.event_publisher]


@inject
def get_create_plan_use_case(
    session: SessionDep,
    factory: Callable[..., CreatePlanUseCase] = Depends(
        Provide[Container.symphony.create_plan_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> CreatePlanUseCase:
    return factory(
        uow=SQLAlchemySymphonyUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_get_plan_use_case(
    session: SessionDep,
    factory: Callable[..., GetPlanUseCase] = Depends(
        Provide[Container.symphony.get_plan_use_case.provider]
    ),
) -> GetPlanUseCase:
    return factory(uow=SQLAlchemySymphonyUnitOfWork(session))


@inject
def get_list_plans_for_run_use_case(
    session: SessionDep,
    factory: Callable[..., ListPlansForRunUseCase] = Depends(
        Provide[Container.symphony.list_plans_for_run_use_case.provider]
    ),
) -> ListPlansForRunUseCase:
    return factory(uow=SQLAlchemySymphonyUnitOfWork(session))


@inject
def get_approve_plan_use_case(
    session: SessionDep,
    factory: Callable[..., ApprovePlanUseCase] = Depends(
        Provide[Container.symphony.approve_plan_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> ApprovePlanUseCase:
    return factory(
        uow=SQLAlchemySymphonyUnitOfWork(session),
        event_publisher=publisher,
    )


@inject
def get_reject_plan_use_case(
    session: SessionDep,
    factory: Callable[..., RejectPlanUseCase] = Depends(
        Provide[Container.symphony.reject_plan_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(core_event_publisher),
) -> RejectPlanUseCase:
    return factory(
        uow=SQLAlchemySymphonyUnitOfWork(session),
        event_publisher=publisher,
    )


CreatePlanUseCaseDep = Annotated[CreatePlanUseCase, Depends(get_create_plan_use_case)]
GetPlanUseCaseDep = Annotated[GetPlanUseCase, Depends(get_get_plan_use_case)]
ListPlansForRunUseCaseDep = Annotated[
    ListPlansForRunUseCase, Depends(get_list_plans_for_run_use_case)
]
ApprovePlanUseCaseDep = Annotated[
    ApprovePlanUseCase, Depends(get_approve_plan_use_case)
]
RejectPlanUseCaseDep = Annotated[RejectPlanUseCase, Depends(get_reject_plan_use_case)]
