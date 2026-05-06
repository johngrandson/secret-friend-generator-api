"""Domain events for the Spec aggregate."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.events import DomainEvent


@dataclass(frozen=True)
class SpecCreated(DomainEvent):
    """Raised when a new Spec version is created for a Run."""

    spec_id: UUID
    run_id: UUID
    version: int


@dataclass(frozen=True)
class SpecApproved(DomainEvent):
    """Raised when a Spec is approved."""

    spec_id: UUID
    run_id: UUID
    version: int
    approved_by: str


@dataclass(frozen=True)
class SpecRejected(DomainEvent):
    """Raised when a Spec is rejected."""

    spec_id: UUID
    run_id: UUID
    version: int
    reason: str
