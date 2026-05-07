"""ApprovedAggregate — base class for write-once approval aggregates.

Spec and Plan share an identical lifecycle: a versioned content blob that
starts pending, can be approved by exactly one operator, or rejected with
a single reason — never both, never twice. This base captures that
invariant so the two aggregates avoid duplicating ~50 lines each.

Subclasses keep their own typed events. They override the three
``_make_*_event`` hooks; the base class drives the state transitions and
calls the hook to obtain the concrete event instance.

The class follows the same dataclass-only pattern as
:class:`src.shared.aggregate_root.AggregateRoot` — no ABC, hooks raise
``NotImplementedError`` to flag missing overrides early.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.contexts.symphony.domain.approval.verdict import ApprovalVerdict
from src.contexts.symphony.domain.validators import (
    ensure_min_version,
    ensure_non_blank,
)
from src.shared.aggregate_root import AggregateRoot
from src.shared.events import DomainEvent


@dataclass
class ApprovedAggregate(AggregateRoot):
    """Aggregate root with write-once approval semantics.

    Subclasses MUST override :meth:`_make_approved_event`,
    :meth:`_make_rejected_event`, and :meth:`_make_created_event` to emit
    their typed domain event variants.
    """

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
        """Approve the aggregate; raises ``ValueError`` if already decided."""
        self._guard_pending()
        ensure_non_blank(by, "Approver identifier")
        self.approved_by = by
        self.approved_at = datetime.now(timezone.utc)
        self.collect_event(self._make_approved_event(by))

    def reject(self, reason: str) -> None:
        """Reject the aggregate; raises ``ValueError`` if already decided."""
        self._guard_pending()
        ensure_non_blank(reason, "Rejection reason")
        self.rejection_reason = reason
        self.collect_event(self._make_rejected_event(reason))

    def apply_verdict(self, verdict: ApprovalVerdict) -> None:
        """Apply a pre-resolved ``ApprovalVerdict`` (ACCEPT/REJECT).

        Convenience for HTTP-style flows where the operator decision arrives
        as a single VO. Internally delegates to :meth:`approve` /
        :meth:`reject` so all write-once invariants and event emission stay
        in one place.
        """
        if verdict.is_accepted():
            self.approve(by=verdict.approver_id)
        else:
            self.reject(reason=verdict.comment or "rejected")

    def _guard_pending(self) -> None:
        if not self.is_pending():
            raise ValueError(
                f"{type(self).__name__} already has a verdict (write-once)."
            )

    def _make_approved_event(self, by: str) -> DomainEvent:
        """Subclass hook: return the typed *Approved* event instance."""
        raise NotImplementedError(
            f"{type(self).__name__} must override _make_approved_event"
        )

    def _make_rejected_event(self, reason: str) -> DomainEvent:
        """Subclass hook: return the typed *Rejected* event instance."""
        raise NotImplementedError(
            f"{type(self).__name__} must override _make_rejected_event"
        )

    def _make_created_event(self) -> DomainEvent:
        """Subclass hook: return the typed *Created* event instance."""
        raise NotImplementedError(
            f"{type(self).__name__} must override _make_created_event"
        )

    @classmethod
    def _build(cls, *, run_id: UUID, version: int, content: str) -> "ApprovedAggregate":
        """Shared factory body: validate inputs and emit the *Created* event.

        Subclasses expose a typed ``create()`` classmethod that delegates
        here; the typed return is preserved by ``cls(...)``.
        """
        ensure_min_version(version)
        ensure_non_blank(content, f"{cls.__name__} content")
        instance = cls(run_id=run_id, version=version, content=content)
        instance.collect_event(instance._make_created_event())
        return instance
