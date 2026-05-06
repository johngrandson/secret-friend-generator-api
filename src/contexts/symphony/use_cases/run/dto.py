"""RunDTO — use-case-layer data transfer object for Run responses."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.contexts.symphony.domain.run.entity import Run


@dataclass(frozen=True)
class RunDTO:
    """Immutable snapshot of a Run for use-case responses."""

    id: UUID
    issue_id: str
    status: str
    workspace_path: str | None
    attempt: int
    error: str | None
    next_attempt_at: datetime | None
    created_at: datetime

    @classmethod
    def from_entity(cls, run: Run) -> "RunDTO":
        """Build a RunDTO from a Run aggregate."""
        return cls(
            id=run.id,
            issue_id=run.issue_id,
            status=str(run.status),
            workspace_path=run.workspace_path,
            attempt=run.attempt,
            error=run.error,
            next_attempt_at=run.next_attempt_at,
            created_at=run.created_at,
        )
