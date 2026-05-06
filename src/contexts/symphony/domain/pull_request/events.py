"""Domain events for the PullRequest aggregate."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.events import DomainEvent


@dataclass(frozen=True)
class PROpened(DomainEvent):
    """Raised when a PR is opened for a Run."""

    pr_id: UUID
    run_id: UUID
    number: int
    url: str


@dataclass(frozen=True)
class PRUpdated(DomainEvent):
    """Raised when an existing PR's metadata is mutated (e.g., draft→ready)."""

    pr_id: UUID
    run_id: UUID
    number: int
