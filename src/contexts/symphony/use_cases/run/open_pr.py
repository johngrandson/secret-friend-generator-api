"""OpenPRUseCase — push branch, open or update GitHub PR, complete the Run.

Caller (F7 OrchestrateRunUseCase) invokes after a successful gate phase
(``Run.status == GATES_PASSED``). Idempotent: re-running on a Run whose
PR already exists triggers ``update_pr`` instead of duplicate creation.

Use case is pure: depends only on ``ICodeHost`` Protocol +
``ISymphonyUnitOfWork`` + domain types. Branch name and title come from
the caller as primitives so the workflow Pydantic config never crosses
this boundary.
"""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from src.contexts.symphony.domain.backlog.issue import Issue
from src.contexts.symphony.domain.code_host import ICodeHost
from src.contexts.symphony.domain.pull_request.entity import PullRequest
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.contexts.symphony.use_cases.run.errors import (
    InvalidRunStateForPRError,
    MissingArtifactError,
)
from src.contexts.symphony.use_cases.run.pr_body_builder import (
    build_pr_body,
    sum_token_usage,
)
from src.contexts.symphony.use_cases.run.status_guards import (
    ensure_run_status,
    ensure_workspace_set,
)
from src.shared.agentic.agent_runner import TokenUsage
from src.shared.event_publisher import IEventPublisher
from src.shared.events import DomainEvent


@dataclass
class OpenPRRequest:
    """Inputs to open a GitHub PR for the run."""

    run_id: UUID
    issue: Issue
    branch: str
    base_branch: str
    title: str
    is_draft: bool = True
    labels: tuple[str, ...] = ()


@dataclass
class OpenPRResponse:
    run: RunDTO | None
    pr_number: int | None
    pr_url: str | None
    was_created: bool
    success: bool = True
    error_message: str | None = None


class OpenPRUseCase:
    """Open or refresh the agent-generated PR for a Run that passed gates."""

    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        code_host: ICodeHost,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._code_host = code_host
        self._publisher = event_publisher

    async def execute(self, request: OpenPRRequest) -> OpenPRResponse:
        response: OpenPRResponse
        events: list[DomainEvent] = []

        async with self._uow:
            run = await self._uow.runs.find_by_id(request.run_id)
            if run is None:
                return OpenPRResponse(
                    None, None, None, False, success=False,
                    error_message="Run not found.",
                )
            ensure_run_status(
                run,
                RunStatus.GATES_PASSED,
                action="OpenPR",
                error_class=InvalidRunStateForPRError,
            )
            workspace_path = ensure_workspace_set(
                run, error_class=InvalidRunStateForPRError
            )

            spec = await self._uow.specs.find_latest_for_run(run.id)
            plan = await self._uow.plans.find_latest_for_run(run.id)
            if spec is None or spec.approved_at is None:
                raise MissingArtifactError("No approved spec for run.")
            if plan is None or plan.approved_at is None:
                raise MissingArtifactError("No approved plan for run.")

            gate_results = await self._uow.gate_results.find_by_run(run.id)
            sessions = await self._uow.agent_sessions.list_by_run(run.id)
            total_usage = sum_token_usage(s.usage for s in sessions) \
                if sessions else TokenUsage()
            model = sessions[-1].model if sessions else "unknown"

            body = build_pr_body(
                issue=request.issue,
                spec_content=spec.content,
                plan_content=plan.content,
                gate_results=gate_results,
                total_usage=total_usage,
                model=model,
            )

            workspace = Path(workspace_path)
            await self._code_host.push_branch(
                branch=request.branch, workspace=workspace
            )
            existing = await self._code_host.find_pr_for_branch(
                branch=request.branch, workspace=workspace
            )

            if existing is None:
                created = await self._code_host.create_pr(
                    branch=request.branch,
                    base=request.base_branch,
                    title=request.title,
                    body=body,
                    labels=request.labels,
                    draft=request.is_draft,
                    workspace=workspace,
                )
                pr = PullRequest.open(
                    run_id=run.id,
                    number=created.number,
                    url=created.url,
                    branch=request.branch,
                    base_branch=request.base_branch,
                    is_draft=request.is_draft,
                    body=body,
                )
                await self._uow.pull_requests.save(pr)
                was_created = True
                pr_number, pr_url = created.number, created.url
            else:
                await self._code_host.update_pr(
                    pr_number=existing.number,
                    title=request.title,
                    body=body,
                    workspace=workspace,
                )
                pr = PullRequest.open(
                    run_id=run.id,
                    number=existing.number,
                    url=existing.url,
                    branch=request.branch,
                    base_branch=request.base_branch,
                    is_draft=existing.is_draft,
                    body=body,
                )
                await self._uow.pull_requests.update(pr)
                was_created = False
                pr_number, pr_url = existing.number, existing.url

            run.mark_completed()
            saved_run = await self._uow.runs.update(run)

            await self._uow.commit()
            events = run.pull_events() + pr.pull_events()
            response = OpenPRResponse(
                run=RunDTO.from_entity(saved_run),
                pr_number=pr_number,
                pr_url=pr_url,
                was_created=was_created,
            )

        if events:
            await self._publisher.publish(events)
        return response
