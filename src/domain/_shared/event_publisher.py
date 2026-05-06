"""IEventPublisher — output port for publishing domain events."""

from typing import Protocol, runtime_checkable

from src.domain._shared.events import DomainEvent


@runtime_checkable
class IEventPublisher(Protocol):
    """Structural interface for publishing domain events after persistence."""

    async def publish(self, events: list[DomainEvent]) -> None: ...
