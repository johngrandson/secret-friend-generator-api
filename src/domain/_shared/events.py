"""Base domain event — pure Python, no framework dependencies."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Immutable base for all domain events.

    Subclasses must be @dataclass(frozen=True) and declare their own fields.
    event_id and occurred_at are auto-generated and excluded from __init__.
    """

    event_id: UUID = field(default_factory=uuid4, init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), init=False
    )
