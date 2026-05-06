"""SpecDTO — use-case-layer data transfer object for Spec responses."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.contexts.symphony.domain.spec.entity import Spec


@dataclass(frozen=True)
class SpecDTO:
    """Immutable snapshot of a Spec for use-case responses."""

    id: UUID
    run_id: UUID
    version: int
    content: str
    approved_at: datetime | None
    approved_by: str | None
    rejection_reason: str | None
    created_at: datetime

    @classmethod
    def from_entity(cls, spec: Spec) -> "SpecDTO":
        """Build a SpecDTO from a Spec aggregate."""
        return cls(
            id=spec.id,
            run_id=spec.run_id,
            version=spec.version,
            content=spec.content,
            approved_at=spec.approved_at,
            approved_by=spec.approved_by,
            rejection_reason=spec.rejection_reason,
            created_at=spec.created_at,
        )
