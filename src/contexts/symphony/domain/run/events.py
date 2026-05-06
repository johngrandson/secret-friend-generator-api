"""Domain events for the Run aggregate."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.events import DomainEvent


@dataclass(frozen=True)
class RunStarted(DomainEvent):
    """Raised when a new Run is created and enters the pipeline."""

    run_id: UUID
    issue_id: str


@dataclass(frozen=True)
class RunStatusChanged(DomainEvent):
    """Raised when the Run transitions from one status to another."""

    run_id: UUID
    from_status: str
    to_status: str


@dataclass(frozen=True)
class RunFailed(DomainEvent):
    """Raised when the Run is marked as failed."""

    run_id: UUID
    error: str
    attempt: int


@dataclass(frozen=True)
class RunCompleted(DomainEvent):
    """Raised when the Run reaches the DONE terminal state."""

    run_id: UUID
