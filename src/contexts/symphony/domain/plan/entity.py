"""Plan entity — versioned execution plan aggregate with write-once approval."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.shared.aggregate_root import AggregateRoot
from src.contexts.symphony.domain.plan.events import (
    PlanApproved,
    PlanCreated,
    PlanRejected,
)


@dataclass
class Plan(AggregateRoot):
    """Aggregate root representing a versioned execution plan."""

    run_id: UUID
    version: int
    content: str
    id: UUID = field(default_factory=uuid4)
    approved_at: datetime | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_pending(self) -> bool:
        """Return True when no verdict has been recorded yet."""
        return self.approved_at is None and self.rejection_reason is None

    def approve(self, by: str) -> None:
        """Approve the plan; raises ValueError if already decided (write-once)."""
        if not self.is_pending():
            raise ValueError("Plan already has a verdict (write-once).")
        if not by.strip():
            raise ValueError("Approver identifier must not be blank.")
        self.approved_by = by
        self.approved_at = datetime.now(timezone.utc)
        self.collect_event(
            PlanApproved(
                plan_id=self.id,
                run_id=self.run_id,
                version=self.version,
                approved_by=by,
            )
        )

    def reject(self, reason: str) -> None:
        """Reject the plan; raises ValueError if already decided (write-once)."""
        if not self.is_pending():
            raise ValueError("Plan already has a verdict (write-once).")
        if not reason.strip():
            raise ValueError("Rejection reason must not be blank.")
        self.rejection_reason = reason
        self.collect_event(
            PlanRejected(
                plan_id=self.id,
                run_id=self.run_id,
                version=self.version,
                reason=reason,
            )
        )

    @classmethod
    def create(cls, run_id: UUID, version: int, content: str) -> "Plan":
        """Factory — validates version >= 1 and non-empty content."""
        if version < 1:
            raise ValueError("Version must be >= 1.")
        if not content.strip():
            raise ValueError("Plan content must not be blank.")
        plan = cls(run_id=run_id, version=version, content=content)
        plan.collect_event(PlanCreated(plan_id=plan.id, run_id=run_id, version=version))
        return plan
