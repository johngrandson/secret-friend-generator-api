"""AggregateRoot — base class for aggregate roots with event tracking."""

from dataclasses import dataclass, field

from src.shared.events import DomainEvent


@dataclass
class AggregateRoot:
    """Base for aggregate roots.

    Tracks pending domain events collected during state changes.
    Call pull_events() after persistence to retrieve and clear them.
    """

    _events: list[DomainEvent] = field(
        init=False, default_factory=list, repr=False, compare=False
    )

    def collect_event(self, event: DomainEvent) -> None:
        """Append an event to the pending list."""
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Return all pending events and clear the internal list."""
        events, self._events = self._events, []
        return events
