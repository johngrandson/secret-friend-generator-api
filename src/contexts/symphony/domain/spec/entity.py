"""Spec entity — versioned design blueprint aggregate with write-once approval."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.symphony.domain.approval.aggregate import ApprovedAggregate
from src.contexts.symphony.domain.spec.events import (
    SpecApproved,
    SpecCreated,
    SpecRejected,
)
from src.shared.events import DomainEvent


@dataclass
class Spec(ApprovedAggregate):
    """Aggregate root representing a versioned design specification."""

    def _make_approved_event(self, by: str) -> DomainEvent:
        return SpecApproved(
            spec_id=self.id,
            run_id=self.run_id,
            version=self.version,
            approved_by=by,
        )

    def _make_rejected_event(self, reason: str) -> DomainEvent:
        return SpecRejected(
            spec_id=self.id,
            run_id=self.run_id,
            version=self.version,
            reason=reason,
        )

    def _make_created_event(self) -> DomainEvent:
        return SpecCreated(spec_id=self.id, run_id=self.run_id, version=self.version)

    @classmethod
    def create(cls, run_id: UUID, version: int, content: str) -> "Spec":
        """Factory — validates version >= 1 and non-empty content."""
        return cls._build(run_id=run_id, version=version, content=content)  # type: ignore[return-value]
