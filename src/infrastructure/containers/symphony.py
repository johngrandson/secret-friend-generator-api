"""Symphony bounded-context container — UoW + use case providers for run/spec/plan.

Cross-cutting dependencies (event_publisher, settings) flow in from the root
container. The UoW is a Factory so each request gets a fresh instance with its
own session.

Pipeline-specific adapters (agent runner, workspace manager, code host, gate
runner, backlog adapter) derive their configs from a lazily loaded
:class:`WorkflowDefinition`. Resolution order:
  1. ``SYMPHONY_WORKFLOW_PATH`` env var (explicit path)
  2. First ``*.md`` file found in ``WORKFLOWS_DIR`` (auto-discovery)
  3. RuntimeError if neither yields a file.
"""

import logging
from pathlib import Path

from dependency_injector import containers, providers

from src.contexts.symphony.adapters.code_host.github.adapter import GitHubCodeHost
from src.contexts.symphony.adapters.gates.ci import CIGate
from src.contexts.symphony.domain.harness_config import HarnessConfig
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
from src.contexts.symphony.use_cases.run.cancel import CancelRunUseCase
from src.contexts.symphony.use_cases.run.create import CreateRunUseCase
from src.contexts.symphony.use_cases.run.delete import DeleteRunUseCase
from src.contexts.symphony.use_cases.run.execute import (
    AgentEventHook,
    ExecuteRunUseCase,
)
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
from src.infrastructure.adapters.events.redis_run_event_bus import RedisRunEventBus
from src.infrastructure.adapters.workflow.loader import load_workflow
from src.infrastructure.adapters.workflow.schemas import WorkflowDefinition
from src.infrastructure.adapters.workspace.filesystem import FilesystemWorkspaceManager
from src.shared.agentic.gate import GateRunner

log = logging.getLogger(__name__)


def _load_workflow_or_raise(path: str | None, workflows_dir: str) -> WorkflowDefinition:
    """Load WorkflowDefinition from explicit path or first file in workflows_dir."""
    if path:
        return load_workflow(path)
    candidates = sorted(Path(workflows_dir).glob("*.md"))
    if not candidates:
        raise RuntimeError(
            f"No workflow file found: set SYMPHONY_WORKFLOW_PATH or add a "
            f"*.md file to '{workflows_dir}'."
        )
    log.info("Auto-discovered workflow: %s", candidates[0])
    return load_workflow(candidates[0])


def _build_agent_runner(workflow: WorkflowDefinition) -> ClaudeCodeRunner:
    return ClaudeCodeRunner(config=workflow.config.claude_code)


def _build_workspace_manager(
    workflow: WorkflowDefinition,
) -> FilesystemWorkspaceManager:
    return FilesystemWorkspaceManager(
        workspace_root=workflow.config.workspace.root,
        hooks=workflow.config.hooks,
    )


def _build_gate_runner(ci_gate: CIGate) -> GateRunner[HarnessConfig]:
    return GateRunner[HarnessConfig](gates=[ci_gate])


def _make_agent_event_hook(bus: RedisRunEventBus) -> AgentEventHook:
    return bus.publish


class SymphonyContainer(containers.DeclarativeContainer):
    event_publisher: providers.Dependency[InMemoryEventPublisher] = (
        providers.Dependency()
    )
    config: providers.Dependency = providers.Dependency()

    symphony_uow = providers.Factory(SQLAlchemySymphonyUnitOfWork)

    redis_event_bus = providers.Singleton(
        RedisRunEventBus,
        redis_url=config.provided.REDIS_URL,
    )

    agent_event_hook = providers.Factory(
        _make_agent_event_hook,
        bus=redis_event_bus,
    )

    workflow_definition = providers.Singleton(
        _load_workflow_or_raise,
        path=config.provided.SYMPHONY_WORKFLOW_PATH,
        workflows_dir=config.provided.WORKFLOWS_DIR,
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
    cancel_run_use_case = providers.Factory(
        CancelRunUseCase,
        uow=symphony_uow,
        event_publisher=event_publisher,
    )
    delete_run_use_case = providers.Factory(
        DeleteRunUseCase,
        uow=symphony_uow,
    )

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
        agent_event_hook=agent_event_hook,
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
