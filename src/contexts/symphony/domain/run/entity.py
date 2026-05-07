"""Run entity — aggregate root with status state machine."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.shared.aggregate_root import AggregateRoot
from src.contexts.symphony.domain.run.events import (
    GatesCompleted,
    RunCompleted,
    RunFailed,
    RunStarted,
    RunStatusChanged,
)
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.validators import ensure_non_blank


@dataclass
class Run(AggregateRoot):
    """Aggregate root representing a single pipeline execution run."""

    issue_id: str
    id: UUID = field(default_factory=uuid4)
    status: RunStatus = RunStatus.RECEIVED
    workspace_path: str | None = None
    attempt: int = 1
    error: str | None = None
    next_attempt_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def set_status(
        self, new_status: RunStatus, *, workspace_path: str | None = None
    ) -> None:
        """Transition to a new status; no-op if already in that status."""
        if new_status == self.status:
            return
        old = self.status
        self.status = new_status
        if workspace_path is not None:
            self.workspace_path = workspace_path
        self.collect_event(
            RunStatusChanged(
                run_id=self.id,
                from_status=old.value,
                to_status=new_status.value,
            )
        )

    def mark_failed(self, error: str) -> None:
        """Mark the run as FAILED with a non-blank error message."""
        ensure_non_blank(error, "Failure error message")
        self.status = RunStatus.FAILED
        self.error = error
        self.collect_event(RunFailed(run_id=self.id, error=error, attempt=self.attempt))

    def mark_retry_pending(self, *, error: str, next_attempt_at: datetime) -> None:
        """Mark the run as RETRY_PENDING; caller scheduler picks it up later.

        Emits both RunStatusChanged (for orchestration) and RunFailed (for
        audit/metrics — retry-pending is a failure of this attempt).
        """
        ensure_non_blank(error, "Retry error message")
        old = self.status
        self.status = RunStatus.RETRY_PENDING
        self.error = error
        self.next_attempt_at = next_attempt_at
        self.collect_event(
            RunStatusChanged(
                run_id=self.id,
                from_status=old.value,
                to_status=RunStatus.RETRY_PENDING.value,
            )
        )
        self.collect_event(
            RunFailed(run_id=self.id, error=error, attempt=self.attempt)
        )

    def mark_completed(self) -> None:
        """Transition to DONE terminal state."""
        self.status = RunStatus.DONE
        self.collect_event(RunCompleted(run_id=self.id))

    def resume_from_retry(self) -> None:
        """Re-arm a RETRY_PENDING run for another attempt.

        Transitions status back to PLAN_APPROVED (the gate just before
        ExecuteRunUseCase) so the orchestrator can re-dispatch the agent.
        Bumps ``attempt``, clears ``error`` and ``next_attempt_at``.
        Raises if called outside RETRY_PENDING.
        """
        if self.status != RunStatus.RETRY_PENDING:
            raise ValueError(
                f"resume_from_retry requires status=RETRY_PENDING; got {self.status}"
            )
        old = self.status
        self.status = RunStatus.PLAN_APPROVED
        self.attempt += 1
        self.error = None
        self.next_attempt_at = None
        self.collect_event(
            RunStatusChanged(
                run_id=self.id,
                from_status=old.value,
                to_status=RunStatus.PLAN_APPROVED.value,
            )
        )

    def complete_gates(self, *, all_passed: bool) -> None:
        """Settle the gate phase: status → GATES_PASSED or GATES_FAILED.

        Always emits ``GatesCompleted`` so observers see the outcome
        regardless of which way the verdict went.
        """
        old = self.status
        new_status = (
            RunStatus.GATES_PASSED if all_passed else RunStatus.GATES_FAILED
        )
        self.status = new_status
        self.collect_event(
            RunStatusChanged(
                run_id=self.id,
                from_status=old.value,
                to_status=new_status.value,
            )
        )
        self.collect_event(
            GatesCompleted(run_id=self.id, all_passed=all_passed)
        )

    @classmethod
    def create(cls, issue_id: str) -> "Run":
        """Factory — validates issue_id and emits RunStarted."""
        ensure_non_blank(issue_id, "Issue identifier")
        run = cls(issue_id=issue_id)
        run.collect_event(RunStarted(run_id=run.id, issue_id=issue_id))
        return run
