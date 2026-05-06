"""Run entity — aggregate root with status state machine."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.shared.aggregate_root import AggregateRoot
from src.contexts.symphony.domain.run.events import (
    RunCompleted,
    RunFailed,
    RunStarted,
    RunStatusChanged,
)
from src.contexts.symphony.domain.run.status import RunStatus


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
        if not error.strip():
            raise ValueError("Failure error message must not be blank.")
        self.status = RunStatus.FAILED
        self.error = error
        self.collect_event(RunFailed(run_id=self.id, error=error, attempt=self.attempt))

    def mark_completed(self) -> None:
        """Transition to DONE terminal state."""
        self.status = RunStatus.DONE
        self.collect_event(RunCompleted(run_id=self.id))

    @classmethod
    def create(cls, issue_id: str) -> "Run":
        """Factory — validates issue_id and emits RunStarted."""
        if not issue_id.strip():
            raise ValueError("Issue identifier must not be blank.")
        run = cls(issue_id=issue_id)
        run.collect_event(RunStarted(run_id=run.id, issue_id=issue_id))
        return run
