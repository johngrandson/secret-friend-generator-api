"""DispatchRunUseCase — one tick that decides what to do next.

Decision tree (origem):
  1. ``count_active`` >= max_concurrent → BUSY (do nothing this tick).
  2. Any due retry (``find_due_retries(now)``) → re-arm oldest, return
     ``DISPATCHED_RETRY``.
  3. Any fresh issue from the backlog adapter not already running → start
     a new Run via ``StartRunUseCase``, return ``DISPATCHED_NEW``.
  4. Otherwise → IDLE.

Use case is pure: depends on Protocols (``ISymphonyUnitOfWork``,
``IBacklogAdapter``, ``StartRunUseCase``) + domain types. The caller (F8
Celery beat task) loads the workflow once per tick and forwards
primitives.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from src.contexts.symphony.domain.backlog.adapter import IBacklogAdapter
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.start import (
    StartRunRequest,
    StartRunUseCase,
)
from src.shared.event_publisher import IEventPublisher


class DispatchOutcome(StrEnum):
    """One of four classes per tick. Caller surfaces via metrics / logs."""

    BUSY = "busy"
    IDLE = "idle"
    DISPATCHED_NEW = "dispatched_new"
    DISPATCHED_RETRY = "dispatched_retry"


@dataclass
class DispatchRunRequest:
    """One dispatch tick.

    The caller resolves the backlog adapter (per-workflow) and forwards
    the concurrency cap from ``workflow.config.agent.max_concurrent_agents``
    so this use case stays Pydantic-free.
    """

    backlog: IBacklogAdapter
    max_concurrent: int


@dataclass
class DispatchRunResponse:
    outcome: DispatchOutcome
    run_id: UUID | None = None
    issue_identifier: str | None = None


class DispatchRunUseCase:
    """One tick: pick the highest-priority work and dispatch it."""

    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        start_run_use_case: StartRunUseCase,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._start_run = start_run_use_case
        self._publisher = event_publisher

    async def execute(self, request: DispatchRunRequest) -> DispatchRunResponse:
        if request.max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")

        async with self._uow:
            in_flight = await self._uow.runs.count_active()
            if in_flight >= request.max_concurrent:
                return DispatchRunResponse(outcome=DispatchOutcome.BUSY)

            due = await self._uow.runs.find_due_retries(datetime.now(timezone.utc))
            if due:
                pick = due[0]  # repository orders by next_attempt_at ascending
                pick.resume_from_retry()
                saved = await self._uow.runs.update(pick)
                await self._uow.commit()
                events = pick.pull_events()
                pick_id = saved.id
                pick_identifier = saved.issue_id
            else:
                events = []
                pick_id = None
                pick_identifier = None
                active_identifiers = set(await self._uow.runs.list_active_identifiers())

        if events:
            await self._publisher.publish(events)
        if pick_id is not None:
            return DispatchRunResponse(
                outcome=DispatchOutcome.DISPATCHED_RETRY,
                run_id=pick_id,
                issue_identifier=pick_identifier,
            )

        all_issues = await request.backlog.fetch_active_issues()
        eligible = [i for i in all_issues if i.identifier not in active_identifiers]
        if not eligible:
            return DispatchRunResponse(outcome=DispatchOutcome.IDLE)

        # Lower priority enum value = higher urgency (URGENT=1 < HIGH=2 < ...).
        chosen = min(eligible, key=lambda i: (i.priority.value, i.created_at))
        start_resp = await self._start_run.execute(StartRunRequest(issue=chosen))
        if not start_resp.success or start_resp.run is None:
            return DispatchRunResponse(outcome=DispatchOutcome.IDLE)
        return DispatchRunResponse(
            outcome=DispatchOutcome.DISPATCHED_NEW,
            run_id=start_resp.run.id,
            issue_identifier=chosen.identifier,
        )
