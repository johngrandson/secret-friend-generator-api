"""GenerateSpecUseCase — orchestrate workspace, agent runner, and Spec aggregate.

The agent writes ``.symphony/spec.md`` inside the per-issue workspace; this
use case validates the artifact, persists a new Spec version, marks the
Run as ``SPEC_PENDING``, and emits domain events.

Use case is pure: it depends only on Protocols (``IAgentRunner``,
``IWorkspaceManager``, ``ISymphonyUnitOfWork``, ``IEventPublisher``) and
domain types. No FastAPI / SQLAlchemy / framework imports.
"""

from dataclasses import dataclass
from pathlib import Path
from string import Template
from uuid import UUID

from src.contexts.symphony.domain.backlog.issue import Issue
from src.contexts.symphony.domain.constants import SPEC_FILENAME
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.artifact_io import read_artifact_file
from src.contexts.symphony.use_cases.run.errors import SpecFileMissingError
from src.contexts.symphony.use_cases.run.issue_template_context import (
    build_issue_template_context,
)
from src.contexts.symphony.use_cases.run.version_helpers import next_version
from src.contexts.symphony.use_cases.spec.dto import SpecDTO
from src.contexts.symphony.use_cases.spec.validate import (
    SpecStructureError,
    validate_spec_content,
)
from src.shared.agentic.agent_runner import AgentRunnerError, IAgentRunner
from src.shared.agentic.workspace import IWorkspaceManager
from src.shared.event_publisher import IEventPublisher

PROMPT_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "spec.md"


@dataclass
class GenerateSpecRequest:
    """Inputs for spec generation. ``issue`` carries all template fields."""

    run_id: UUID
    issue: Issue


@dataclass
class GenerateSpecResponse:
    spec: SpecDTO | None
    success: bool
    error_message: str | None = None


class GenerateSpecUseCase:
    """Run the agent in a workspace, persist the generated SPEC, advance Run."""

    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        agent_runner: IAgentRunner,
        workspace_manager: IWorkspaceManager,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._agent_runner = agent_runner
        self._workspace_manager = workspace_manager
        self._publisher = event_publisher

    async def execute(
        self, request: GenerateSpecRequest
    ) -> GenerateSpecResponse:
        async with self._uow:
            run = await self._uow.runs.find_by_id(request.run_id)
            if run is None:
                return GenerateSpecResponse(None, False, "Run not found.")

            workspace = await self._workspace_manager.ensure(
                request.issue.identifier
            )
            prompt = render_spec_prompt(request.issue)

            try:
                turn = await self._agent_runner.run_turn(
                    prompt=prompt, workspace=workspace.path
                )
            except AgentRunnerError as exc:
                return GenerateSpecResponse(None, False, str(exc))

            try:
                content = read_artifact_file(
                    workspace_root=workspace.path,
                    filename=SPEC_FILENAME,
                    missing_error=SpecFileMissingError,
                    session_id=turn.session_id,
                )
                validate_spec_content(content)
            except (SpecFileMissingError, SpecStructureError) as exc:
                return GenerateSpecResponse(None, False, str(exc))

            previous = await self._uow.specs.find_latest_for_run(run.id)
            spec = Spec.create(
                run_id=run.id, version=next_version(previous), content=content
            )
            saved = await self._uow.specs.save(spec)

            run.set_status(
                RunStatus.SPEC_PENDING, workspace_path=str(workspace.path)
            )
            await self._uow.runs.update(run)

            await self._uow.commit()
            events = spec.pull_events() + run.pull_events()

        if events:
            await self._publisher.publish(events)
        return GenerateSpecResponse(SpecDTO.from_entity(saved), True)


def render_spec_prompt(issue: Issue) -> str:
    """Substitute issue fields into the canonical SPEC prompt template."""
    template = Template(PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.safe_substitute(build_issue_template_context(issue))
