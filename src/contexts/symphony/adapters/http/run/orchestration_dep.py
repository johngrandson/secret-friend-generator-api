"""Composite dependency for the OrchestrateRun HTTP route.

Building :class:`OrchestrateRunUseCase` per request takes the same
request-scoped UoW + the workflow-derived sub-use-cases. Bundling
the wiring here keeps the route handler thin.
"""

from collections.abc import Callable
from typing import Annotated, Any

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.contexts.symphony.domain.backlog.adapter import IBacklogAdapter
from src.contexts.symphony.use_cases.orchestration.orchestrate_run import (
    OrchestrateRunUseCase,
)
from src.contexts.symphony.use_cases.plan.generate import GeneratePlanUseCase
from src.contexts.symphony.use_cases.run.execute import ExecuteRunUseCase
from src.contexts.symphony.use_cases.run.open_pr import OpenPRUseCase
from src.contexts.symphony.use_cases.run.run_gates import RunGatesUseCase
from src.contexts.symphony.use_cases.spec.generate import GenerateSpecUseCase
from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.infrastructure.adapters.workflow.schemas import WorkflowDefinition
from src.infrastructure.containers import Container
from src.infrastructure.database import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@inject
def get_orchestrate_run_use_case(
    session: SessionDep,
    generate_spec_factory: Callable[..., GenerateSpecUseCase] = Depends(
        Provide[Container.symphony.generate_spec_use_case.provider]
    ),
    generate_plan_factory: Callable[..., GeneratePlanUseCase] = Depends(
        Provide[Container.symphony.generate_plan_use_case.provider]
    ),
    execute_run_factory: Callable[..., ExecuteRunUseCase] = Depends(
        Provide[Container.symphony.execute_run_use_case.provider]
    ),
    run_gates_factory: Callable[..., RunGatesUseCase] = Depends(
        Provide[Container.symphony.run_gates_use_case.provider]
    ),
    open_pr_factory: Callable[..., OpenPRUseCase] = Depends(
        Provide[Container.symphony.open_pr_use_case.provider]
    ),
    orchestrate_factory: Callable[..., OrchestrateRunUseCase] = Depends(
        Provide[Container.symphony.orchestrate_run_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(
        Provide[Container.core.event_publisher]
    ),
) -> OrchestrateRunUseCase:
    """Build OrchestrateRunUseCase with all sub-use-cases sharing one request UoW."""
    uow = SQLAlchemySymphonyUnitOfWork(session)
    sub_kwargs: dict[str, Any] = {"uow": uow, "event_publisher": publisher}
    return orchestrate_factory(
        uow=uow,
        generate_spec_use_case=generate_spec_factory(**sub_kwargs),
        generate_plan_use_case=generate_plan_factory(**sub_kwargs),
        execute_run_use_case=execute_run_factory(**sub_kwargs),
        run_gates_use_case=run_gates_factory(**sub_kwargs),
        open_pr_use_case=open_pr_factory(**sub_kwargs),
        event_publisher=publisher,
    )


@inject
def get_backlog_adapter(
    backlog: IBacklogAdapter = Depends(
        Provide[Container.symphony.linear_backlog_adapter]
    ),
) -> IBacklogAdapter:
    return backlog


@inject
def get_workflow_definition(
    workflow: WorkflowDefinition = Depends(
        Provide[Container.symphony.workflow_definition]
    ),
) -> WorkflowDefinition:
    return workflow


OrchestrateRunUseCaseDep = Annotated[
    OrchestrateRunUseCase, Depends(get_orchestrate_run_use_case)
]
BacklogAdapterDep = Annotated[IBacklogAdapter, Depends(get_backlog_adapter)]
WorkflowDefinitionDep = Annotated[
    WorkflowDefinition, Depends(get_workflow_definition)
]
