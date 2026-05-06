"""Domain events for the Plan aggregate."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.events import DomainEvent


@dataclass(frozen=True)
class PlanCreated(DomainEvent):
    """Raised when a new Plan version is created for a Run."""

    plan_id: UUID
    run_id: UUID
    version: int


@dataclass(frozen=True)
class PlanApproved(DomainEvent):
    """Raised when a Plan is approved."""

    plan_id: UUID
    run_id: UUID
    version: int
    approved_by: str


@dataclass(frozen=True)
class PlanRejected(DomainEvent):
    """Raised when a Plan is rejected."""

    plan_id: UUID
    run_id: UUID
    version: int
    reason: str
