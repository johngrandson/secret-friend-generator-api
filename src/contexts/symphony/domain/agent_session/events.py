"""Domain events for the AgentSession aggregate."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.agentic.agent_runner import TokenUsage
from src.shared.events import DomainEvent


@dataclass(frozen=True)
class AgentSessionStarted(DomainEvent):
    """Raised when a new agent session is opened against a Run."""

    session_id: UUID
    run_id: UUID
    model: str


@dataclass(frozen=True)
class AgentSessionCompleted(DomainEvent):
    """Raised when the agent session terminates successfully with token usage."""

    session_id: UUID
    run_id: UUID
    usage: TokenUsage


@dataclass(frozen=True)
class AgentSessionFailed(DomainEvent):
    """Raised when the agent session terminates with a non-recoverable error."""

    session_id: UUID
    run_id: UUID
    error: str
