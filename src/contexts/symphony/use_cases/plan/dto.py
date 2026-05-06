"""PlanDTO — use-case-layer data transfer object for Plan responses."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.contexts.symphony.domain.plan.entity import Plan


@dataclass(frozen=True)
class PlanDTO:
    """Immutable snapshot of a Plan for use-case responses."""

    id: UUID
    run_id: UUID
    version: int
    content: str
    approved_at: datetime | None
    approved_by: str | None
    rejection_reason: str | None
    created_at: datetime

    @classmethod
    def from_entity(cls, plan: Plan) -> "PlanDTO":
        """Build a PlanDTO from a Plan aggregate."""
        return cls(
            id=plan.id,
            run_id=plan.run_id,
            version=plan.version,
            content=plan.content,
            approved_at=plan.approved_at,
            approved_by=plan.approved_by,
            rejection_reason=plan.rejection_reason,
            created_at=plan.created_at,
        )
