"""ExecuteRunUseCase — invoke the agent for the run, persist AgentSession.

Load-bearing invariant: this use case is one UoW transaction. Failures
are captured, classified via :func:`classify_failure` from the kernel
retry primitive, and persisted as Run state changes (RETRY_PENDING /
FAILED). The caller (F7 OrchestrateRunUseCase) re-reads Run state on
every tick — never iterates this in memory.

Use case stays pure: depends on Protocols + domain only. The agent
runner is wired with its own config at composition time (F8); the use
case knows nothing about claude_code internals.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import UUID

AgentEventHook = Callable[[UUID, dict[str, Any]], Awaitable[None]]

from src.contexts.symphony.domain.agent_session.entity import AgentSession
from src.contexts.symphony.domain.backlog.issue import Issue
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.contexts.symphony.use_cases.run.errors import InvalidRunStateError
from src.contexts.symphony.use_cases.run.prompt_renderer import render_run_prompt
from src.contexts.symphony.use_cases.run.status_guards import (
    ensure_run_status,
    ensure_workspace_set,
)
from src.shared.agentic.agent_runner import (
    AgentEventCallback,
    AgentRunnerError,
    IAgentRunner,
    TokenUsage,
    TurnResult,
)
from src.shared.agentic.retry import RetryConfig, classify_failure, compute_delay
from src.shared.event_publisher import IEventPublisher
from src.shared.events import DomainEvent


class ExecuteOutcome(StrEnum):
    """Result classes returned to the caller; drive next-tick decisions."""

    SUCCESS = "success"
    RETRY_PENDING = "retry_pending"
    FAILED = "failed"


@dataclass
class ExecuteRunRequest:
    """Inputs for one execute attempt.

    ``prompt_template`` is the operator's WORKFLOW.md body. The caller
    (F7 orchestrator) parses the workflow once and forwards the template
    string so this use case stays free of infrastructure imports.
    ``model_name`` is the agent model identifier (e.g. ``claude-sonnet-4-6``)
    captured for AgentSession audit.
    """

    run_id: UUID
    issue: Issue
    prompt_template: str
    model_name: str
    retry_config: RetryConfig | None = None


@dataclass
class ExecuteRunResponse:
    run: RunDTO | None
    outcome: ExecuteOutcome
    session_id: str | None = None
    usage: TokenUsage | None = None
    error_message: str | None = None


class ExecuteRunUseCase:
    """Run the agent against the approved Spec + Plan; persist outcome."""

    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        agent_runner: IAgentRunner,
        event_publisher: IEventPublisher,
        agent_event_hook: AgentEventHook | None = None,
    ) -> None:
        self._uow = uow
        self._agent_runner = agent_runner
        self._publisher = event_publisher
        self._agent_event_hook = agent_event_hook

    async def execute(self, request: ExecuteRunRequest) -> ExecuteRunResponse:
        response: ExecuteRunResponse
        events: list[DomainEvent] = []
        agent_started = False

        try:
            async with self._uow:
                run = await self._uow.runs.find_by_id(request.run_id)
                if run is None:
                    return ExecuteRunResponse(
                        None, ExecuteOutcome.FAILED, error_message="Run not found."
                    )
                ensure_run_status(
                    run,
                    RunStatus.PLAN_APPROVED,
                    action="ExecuteRun",
                    error_class=InvalidRunStateError,
                )
                workspace_path = ensure_workspace_set(
                    run, error_class=InvalidRunStateError
                )

                spec = await self._uow.specs.find_latest_for_run(run.id)
                if spec is None or spec.approved_at is None:
                    return ExecuteRunResponse(
                        None,
                        ExecuteOutcome.FAILED,
                        error_message="No approved spec for run.",
                    )
                plan = await self._uow.plans.find_latest_for_run(run.id)
                if plan is None or plan.approved_at is None:
                    return ExecuteRunResponse(
                        None,
                        ExecuteOutcome.FAILED,
                        error_message="No approved plan for run.",
                    )

                prompt = render_run_prompt(
                    template=request.prompt_template,
                    issue=request.issue,
                    spec_content=spec.content,
                    plan_content=plan.content,
                    attempt=run.attempt,
                )

                session = AgentSession.create(run_id=run.id, model=request.model_name)
                run.set_status(RunStatus.EXECUTE)

                run_id = run.id
                on_event: AgentEventCallback | None = None
                if self._agent_event_hook:
                    hook = self._agent_event_hook

                    async def on_event(event: dict[str, Any]) -> None:
                        await hook(run_id, event)

                agent_started = True
                try:
                    turn = await self._agent_runner.run_turn(
                        prompt=prompt,
                        workspace=Path(workspace_path),
                        session_id=session.session_id,
                        on_event=on_event,
                    )
                except AgentRunnerError as exc:
                    response, events = await self._build_failure_response(
                        exc=exc,
                        run=run,
                        session=session,
                        retry_config=request.retry_config,
                    )
                else:
                    response, events = await self._build_success_response(
                        turn=turn, run=run, session=session
                    )

                await self._uow.commit()

            if events:
                await self._publisher.publish(events)
            return response
        finally:
            if agent_started and self._agent_event_hook:
                await self._agent_event_hook(request.run_id, {"type": "_stream_done"})

    async def _build_success_response(
        self,
        *,
        turn: TurnResult,
        run: Run,
        session: AgentSession,
    ) -> tuple[ExecuteRunResponse, list[DomainEvent]]:
        """Persist success state; collect events (no commit/publish)."""
        session.session_id = turn.session_id
        session.complete(usage=turn.usage)
        await self._uow.agent_sessions.save(session)

        run.mark_executed(session_id=session.id, usage=turn.usage)
        saved_run = await self._uow.runs.update(run)

        events = run.pull_events() + session.pull_events()
        return (
            ExecuteRunResponse(
                run=RunDTO.from_entity(saved_run),
                outcome=ExecuteOutcome.SUCCESS,
                session_id=turn.session_id,
                usage=turn.usage,
            ),
            events,
        )

    async def _build_failure_response(
        self,
        *,
        exc: AgentRunnerError,
        run: Run,
        session: AgentSession,
        retry_config: RetryConfig | None,
    ) -> tuple[ExecuteRunResponse, list[DomainEvent]]:
        """Classify failure, advance Run; collect events (no commit/publish)."""
        kind = classify_failure(exc)
        session.fail(str(exc))
        await self._uow.agent_sessions.save(session)

        if kind is None:
            run.mark_failed(str(exc))
            outcome = ExecuteOutcome.FAILED
        else:
            cfg = retry_config or RetryConfig()
            delay_ms = compute_delay(attempt=run.attempt + 1, kind=kind, config=cfg)
            next_at = datetime.now(timezone.utc) + timedelta(milliseconds=delay_ms)
            run.mark_retry_pending(error=str(exc), next_attempt_at=next_at)
            outcome = ExecuteOutcome.RETRY_PENDING

        saved_run = await self._uow.runs.update(run)
        events = run.pull_events() + session.pull_events()
        return (
            ExecuteRunResponse(
                run=RunDTO.from_entity(saved_run),
                outcome=outcome,
                error_message=str(exc),
            ),
            events,
        )
