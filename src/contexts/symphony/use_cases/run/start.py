"""StartRunUseCase — create a Run + ensure its workspace.

Entry point of the symphony pipeline. After ``StartRunUseCase`` commits,
downstream use cases (``GenerateSpec``, ``GeneratePlan``, ``ExecuteRun``)
**re-read** the Run state from persistence per the load-bearing
invariant: orchestration NEVER iterates in-memory between sub-use-cases.

Use case is pure: depends only on Protocols
(``ISymphonyUnitOfWork``, ``IWorkspaceManager``, ``IEventPublisher``)
plus domain types. MCP config materialization and workflow parsing live
in the orchestrator/composition layer (F7/F8); we keep this use case
free of any infrastructure import to satisfy the ``use-cases-purity``
import-linter contract.
"""

from dataclasses import dataclass

from src.contexts.symphony.domain.backlog.issue import Issue
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.shared.agentic.workspace import IWorkspaceManager
from src.shared.event_publisher import IEventPublisher


@dataclass
class StartRunRequest:
    """Inputs for starting a new Run pipeline."""

    issue: Issue


@dataclass
class StartRunResponse:
    run: RunDTO | None
    workspace_path: str | None
    success: bool
    error_message: str | None = None


class StartRunUseCase:
    """Create a Run, ensure its workspace, advance status to GEN_SPEC."""

    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        workspace_manager: IWorkspaceManager,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._workspace_manager = workspace_manager
        self._publisher = event_publisher

    async def execute(self, request: StartRunRequest) -> StartRunResponse:
        try:
            run = Run.create(issue_id=request.issue.identifier)
        except ValueError as exc:
            return StartRunResponse(None, None, False, str(exc))

        async with self._uow:
            workspace = await self._workspace_manager.ensure(
                request.issue.identifier
            )
            run.set_status(
                RunStatus.GEN_SPEC, workspace_path=str(workspace.path)
            )
            saved = await self._uow.runs.save(run)
            await self._uow.commit()
            events = run.pull_events()

        if events:
            await self._publisher.publish(events)
        return StartRunResponse(
            run=RunDTO.from_entity(saved),
            workspace_path=str(workspace.path),
            success=True,
        )
