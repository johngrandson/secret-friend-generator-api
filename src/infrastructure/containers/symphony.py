"""Symphony bounded-context container — UoW + use case providers for run/spec/plan.

Cross-cutting dependencies (event_publisher) flow in from the root container.
The UoW is a Factory so each request gets a fresh instance with its own session.
"""

import logging

from dependency_injector import containers, providers

from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.contexts.symphony.adapters.backlog.config import TrackerConfig
from src.contexts.symphony.adapters.backlog.linear import LinearBacklogAdapter
from src.contexts.symphony.use_cases.run.create import CreateRunUseCase
from src.contexts.symphony.use_cases.run.get import GetRunUseCase
from src.contexts.symphony.use_cases.run.list import ListRunsUseCase
from src.contexts.symphony.use_cases.spec.approve import ApproveSpecUseCase
from src.contexts.symphony.use_cases.spec.create import CreateSpecUseCase
from src.contexts.symphony.use_cases.spec.get import GetSpecUseCase
from src.contexts.symphony.use_cases.spec.list_for_run import ListSpecsForRunUseCase
from src.contexts.symphony.use_cases.spec.reject import RejectSpecUseCase
from src.contexts.symphony.use_cases.plan.approve import ApprovePlanUseCase
from src.contexts.symphony.use_cases.plan.create import CreatePlanUseCase
from src.contexts.symphony.use_cases.plan.get import GetPlanUseCase
from src.contexts.symphony.use_cases.plan.list_for_run import ListPlansForRunUseCase
from src.contexts.symphony.use_cases.plan.reject import RejectPlanUseCase

log = logging.getLogger(__name__)


def _build_linear_adapter(
    api_key: str | None, project_slug: str | None
) -> LinearBacklogAdapter:
    """Construct a LinearBacklogAdapter from settings values.

    If LINEAR_API_KEY or LINEAR_PROJECT_SLUG are not configured, logs a
    warning and uses placeholder values. The adapter will fail at the
    first real API call with a BacklogAuthError.
    """
    if not api_key or not project_slug:
        log.warning(
            "LINEAR_API_KEY or LINEAR_PROJECT_SLUG not set — "
            "LinearBacklogAdapter will fail on first use."
        )
        api_key = api_key or "not-configured"
        project_slug = project_slug or "not-configured"
    config = TrackerConfig(api_key=api_key, project_slug=project_slug)
    return LinearBacklogAdapter(config)


class SymphonyContainer(containers.DeclarativeContainer):
    event_publisher: providers.Dependency[InMemoryEventPublisher] = (
        providers.Dependency()
    )
    config: providers.Dependency = providers.Dependency()

    symphony_uow = providers.Factory(SQLAlchemySymphonyUnitOfWork)

    linear_backlog_adapter = providers.Singleton(
        _build_linear_adapter,
        api_key=config.provided.LINEAR_API_KEY,
        project_slug=config.provided.LINEAR_PROJECT_SLUG,
    )

    # --- Run ---
    create_run_use_case = providers.Factory(
        CreateRunUseCase,
        uow=symphony_uow,
        event_publisher=event_publisher,
    )
    get_run_use_case = providers.Factory(
        GetRunUseCase,
        uow=symphony_uow,
    )
    list_runs_use_case = providers.Factory(
        ListRunsUseCase,
        uow=symphony_uow,
    )

    # --- Spec ---
    create_spec_use_case = providers.Factory(
        CreateSpecUseCase,
        uow=symphony_uow,
        event_publisher=event_publisher,
    )
    get_spec_use_case = providers.Factory(
        GetSpecUseCase,
        uow=symphony_uow,
    )
    list_specs_for_run_use_case = providers.Factory(
        ListSpecsForRunUseCase,
        uow=symphony_uow,
    )
    approve_spec_use_case = providers.Factory(
        ApproveSpecUseCase,
        uow=symphony_uow,
        event_publisher=event_publisher,
    )
    reject_spec_use_case = providers.Factory(
        RejectSpecUseCase,
        uow=symphony_uow,
        event_publisher=event_publisher,
    )

    # --- Plan ---
    create_plan_use_case = providers.Factory(
        CreatePlanUseCase,
        uow=symphony_uow,
        event_publisher=event_publisher,
    )
    get_plan_use_case = providers.Factory(
        GetPlanUseCase,
        uow=symphony_uow,
    )
    list_plans_for_run_use_case = providers.Factory(
        ListPlansForRunUseCase,
        uow=symphony_uow,
    )
    approve_plan_use_case = providers.Factory(
        ApprovePlanUseCase,
        uow=symphony_uow,
        event_publisher=event_publisher,
    )
    reject_plan_use_case = providers.Factory(
        RejectPlanUseCase,
        uow=symphony_uow,
        event_publisher=event_publisher,
    )
