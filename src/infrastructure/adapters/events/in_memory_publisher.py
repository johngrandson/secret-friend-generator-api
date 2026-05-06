"""InMemoryEventPublisher — logs domain events via stdlib logging.

Placeholder adapter for IEventPublisher. Swap for a real broker
(Kafka, RabbitMQ, Redis Streams) by implementing the same async publish()
signature and registering in the container.
"""

import logging

from src.shared.events import DomainEvent

logger = logging.getLogger(__name__)


class InMemoryEventPublisher:
    """Implements IEventPublisher structurally (no explicit inheritance)."""

    async def publish(self, events: list[DomainEvent]) -> None:
        for event in events:
            logger.info(
                "domain_event",
                extra={"event": event.__class__.__name__, "data": event},
            )
