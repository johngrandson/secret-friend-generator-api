"""Symphony bounded-context container — UoW + use case providers for run/spec/plan.

Cross-cutting dependencies (event_publisher, settings) flow in from the root
container. The UoW is a Factory so each request gets a fresh instance with its
own session.

Pipeline-specific adapters (agent runner, workspace manager, code host, gate
runner) derive their configs from a lazily loaded :class:`WorkflowDefinition`
keyed by ``Settings.SYMPHONY_WORKFLOW_PATH``. When that env var is unset the
:func:`_load_workflow_or_raise` helper raises at first access — read-only
HTTP routes that never hit the pipeline still work.
"""

import logging

from dependency_injector import containers, providers

from src.contexts.symphony.adapters.backlog.linear import LinearBacklogAdapter
from src.contexts.symphony.adapters.code_host.github.adapter import GitHubCodeHost
from src.contexts.symphony.adapters.gates.ci import CIGate
from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.contexts.symphony.use_cases.dispatch.dispatch_run import DispatchRunUseCase
from src.contexts.symphony.use_cases.orchestration.orchestrate_run import (
    OrchestrateRunUseCase,
)
from src.contexts.symphony.use_cases.plan.approve import ApprovePlanUseCase
from src.contexts.symphony.use_cases.plan.create import CreatePlanUseCase
from src.contexts.symphony.use_cases.plan.generate import GeneratePlanUseCase
from src.contexts.symphony.use_cases.plan.get import GetPlanUseCase
from src.contexts.symphony.use_cases.plan.list_for_run import ListPlansForRunUseCase
from src.contexts.symphony.use_cases.plan.reject import RejectPlanUseCase
from src.contexts.symphony.use_cases.run.create import CreateRunUseCase
from src.contexts.symphony.use_cases.run.execute import ExecuteRunUseCase
from src.contexts.symphony.use_cases.run.get import GetRunUseCase
from src.contexts.symphony.use_cases.run.get_detail import GetRunDetailUseCase
from src.contexts.symphony.use_cases.run.list import ListRunsUseCase
from src.contexts.symphony.use_cases.run.open_pr import OpenPRUseCase
from src.contexts.symphony.use_cases.run.run_gates import RunGatesUseCase
from src.contexts.symphony.use_cases.run.start import StartRunUseCase
from src.contexts.symphony.use_cases.spec.approve import ApproveSpecUseCase
from src.contexts.symphony.use_cases.spec.create import CreateSpecUseCase
from src.contexts.symphony.use_cases.spec.generate import GenerateSpecUseCase
from src.contexts.symphony.use_cases.spec.get import GetSpecUseCase
from src.contexts.symphony.use_cases.spec.list_for_run import ListSpecsForRunUseCase
from src.contexts.symphony.use_cases.spec.reject import RejectSpecUseCase
from src.infrastructure.adapters.agent_runner.claude_code.runner import ClaudeCodeRunner
from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.infrastructure.adapters.workflow.loader import load_workflow
from src.infrastructure.adapters.workflow.schemas import (
    TrackerConfig,
    WorkflowDefinition,
)
from src.infrastructure.adapters.workspace.filesystem import FilesystemWorkspaceManager
from src.shared.agentic.gate import GateRunner

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
    config = TrackerConfig(kind="linear", api_key=api_key, project_slug=project_slug)
    return LinearBacklogAdapter(config)


def _load_workflow_or_raise(path: str | None) -> WorkflowDefinition:
    """Lazy-load the WorkflowDefinition or raise ``SYMPHONY_WORKFLOW_PATH`` is unset."""
    if not path:
        raise RuntimeError(
            "SYMPHONY_WORKFLOW_PATH is not set; symphony pipeline use cases "
            "(generate/execute/orchestrate/dispatch) cannot be constructed."
        )
    return load_workflow(path)


def _build_agent_runner(workflow: WorkflowDefinition) -> ClaudeCodeRunner:
    return ClaudeCodeRunner(config=workflow.config.claude_code)


def _build_workspace_manager(
    workflow: WorkflowDefinition,
) -> FilesystemWorkspaceManager:
    return FilesystemWorkspaceManager(
        workspace_root=workflow.config.workspace.root,
        hooks=workflow.config.hooks,
    )


def _build_gate_runner(ci_gate: CIGate) -> GateRunner:
    return GateRunner(gates=[ci_gate])


class SymphonyContainer(containers.DeclarativeContainer):
    event_publisher: providers.Dependency[InMemoryEventPublisher] = (
        providers.Dependency()
    )
    config: providers.Dependency = providers.Dependency()

    symphony_uow = providers.Factory(SQLAlchemySymphonyUnitOfWork)

    # --- Pipeline adapters ---
    workflow_definition = providers.Singleton(
        _load_workflow_or_raise,
        path=config.provided.SYMPHONY_WORKFLOW_PATH,
    )

    agent_runner = providers.Singleton(
        _build_agent_runner, workflow=workflow_definition
    )

    workspace_manager = providers.Singleton(
        _build_workspace_manager, workflow=workflow_definition
    )

    code_host = providers.Singleton(GitHubCodeHost)

    ci_gate = providers.Singleton(CIGate)

    gate_runner = providers.Singleton(_build_gate_runner, ci_gate=ci_gate)

    linear_backlog_adapter = providers.Singleton(
        _build_linear_adapter,
        api_key=config.provided.LINEAR_API_KEY,
        project_slug=config.provided.LINEAR_PROJECT_SLUG,
    )

    # --- Run (CRUD) ---
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
    get_run_detail_use_case = providers.Factory(
        GetRunDetailUseCase,
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
    generate_spec_use_case = providers.Factory(
        GenerateSpecUseCase,
        uow=symphony_uow,
        agent_runner=agent_runner,
        workspace_manager=workspace_manager,
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
    generate_plan_use_case = providers.Factory(
        GeneratePlanUseCase,
        uow=symphony_uow,
        agent_runner=agent_runner,
        workspace_manager=workspace_manager,
        event_publisher=event_publisher,
    )

    # --- Run pipeline ---
    start_run_use_case = providers.Factory(
        StartRunUseCase,
        uow=symphony_uow,
        workspace_manager=workspace_manager,
        event_publisher=event_publisher,
    )
    execute_run_use_case = providers.Factory(
        ExecuteRunUseCase,
        uow=symphony_uow,
        agent_runner=agent_runner,
        event_publisher=event_publisher,
    )
    run_gates_use_case = providers.Factory(
        RunGatesUseCase,
        uow=symphony_uow,
        gate_runner=gate_runner,
        event_publisher=event_publisher,
    )
    open_pr_use_case = providers.Factory(
        OpenPRUseCase,
        uow=symphony_uow,
        code_host=code_host,
        event_publisher=event_publisher,
    )

    # --- Coordination ---
    orchestrate_run_use_case = providers.Factory(
        OrchestrateRunUseCase,
        uow=symphony_uow,
        generate_spec_use_case=generate_spec_use_case,
        generate_plan_use_case=generate_plan_use_case,
        execute_run_use_case=execute_run_use_case,
        run_gates_use_case=run_gates_use_case,
        open_pr_use_case=open_pr_use_case,
        event_publisher=event_publisher,
    )
    dispatch_run_use_case = providers.Factory(
        DispatchRunUseCase,
        uow=symphony_uow,
        start_run_use_case=start_run_use_case,
        event_publisher=event_publisher,
    )
