"""GeneratePlanUseCase — orchestrate workspace, agent runner, and Plan aggregate.

Mirrors :mod:`...spec.generate` but pulls the latest approved Spec for the
Run and embeds it in the prompt. Without an approved Spec the use case
short-circuits with a typed failure response — plan generation has no
ground truth to work from.
"""

from dataclasses import dataclass
from pathlib import Path
from string import Template
from uuid import UUID

from src.contexts.symphony.domain.backlog.issue import Issue
from src.contexts.symphony.domain.constants import PLAN_FILENAME
from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.plan.dto import PlanDTO
from src.contexts.symphony.use_cases.plan.validate import (
    PlanStructureError,
    validate_plan_content,
)
from src.contexts.symphony.use_cases.run.artifact_io import read_artifact_file
from src.contexts.symphony.use_cases.run.errors import PlanFileMissingError
from src.contexts.symphony.use_cases.run.issue_template_context import (
    build_issue_template_context,
)
from src.contexts.symphony.use_cases.run.version_helpers import next_version
from src.shared.agentic.agent_runner import AgentRunnerError, IAgentRunner
from src.shared.agentic.workspace import IWorkspaceManager
from src.shared.event_publisher import IEventPublisher

PROMPT_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "plan.md"


@dataclass
class GeneratePlanRequest:
    """Inputs for plan generation. ``issue`` carries all template fields."""

    run_id: UUID
    issue: Issue


@dataclass
class GeneratePlanResponse:
    plan: PlanDTO | None
    success: bool
    error_message: str | None = None


class GeneratePlanUseCase:
    """Run the agent against the approved SPEC, persist the new Plan version."""

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
        self, request: GeneratePlanRequest
    ) -> GeneratePlanResponse:
        async with self._uow:
            run = await self._uow.runs.find_by_id(request.run_id)
            if run is None:
                return GeneratePlanResponse(None, False, "Run not found.")

            spec = await self._uow.specs.find_latest_for_run(run.id)
            if spec is None or spec.approved_at is None:
                return GeneratePlanResponse(
                    None, False, "No approved spec for run."
                )

            workspace = await self._workspace_manager.ensure(
                request.issue.identifier
            )
            prompt = render_plan_prompt(
                issue=request.issue, approved_spec=spec.content
            )

            try:
                turn = await self._agent_runner.run_turn(
                    prompt=prompt, workspace=workspace.path
                )
            except AgentRunnerError as exc:
                return GeneratePlanResponse(None, False, str(exc))

            try:
                content = read_artifact_file(
                    workspace_root=workspace.path,
                    filename=PLAN_FILENAME,
                    missing_error=PlanFileMissingError,
                    session_id=turn.session_id,
                )
                validate_plan_content(content)
            except (PlanFileMissingError, PlanStructureError) as exc:
                return GeneratePlanResponse(None, False, str(exc))

            previous = await self._uow.plans.find_latest_for_run(run.id)
            plan = Plan.create(
                run_id=run.id, version=next_version(previous), content=content
            )
            saved = await self._uow.plans.save(plan)

            run.set_status(
                RunStatus.PLAN_PENDING, workspace_path=str(workspace.path)
            )
            await self._uow.runs.update(run)

            await self._uow.commit()
            events = plan.pull_events() + run.pull_events()

        if events:
            await self._publisher.publish(events)
        return GeneratePlanResponse(PlanDTO.from_entity(saved), True)


def render_plan_prompt(*, issue: Issue, approved_spec: str) -> str:
    """Substitute issue fields + approved spec into the plan prompt template."""
    template = Template(PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8"))
    context = build_issue_template_context(
        issue, extra={"approved_spec_content": approved_spec.strip()}
    )
    return template.safe_substitute(context)
