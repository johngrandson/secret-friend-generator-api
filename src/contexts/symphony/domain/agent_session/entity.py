"""AgentSession aggregate root — tracks one Claude/agent session per Run."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.contexts.symphony.domain.agent_session.events import (
    AgentSessionCompleted,
    AgentSessionFailed,
    AgentSessionStarted,
)
from src.shared.agentic.agent_runner import TokenUsage
from src.shared.aggregate_root import AggregateRoot


@dataclass
class AgentSession(AggregateRoot):
    """One agent session for a Run. Token usage accumulates across turns."""

    run_id: UUID
    model: str
    session_id: str | None = None
    id: UUID = field(default_factory=uuid4)
    usage: TokenUsage = field(default_factory=TokenUsage)
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None
    error: str | None = None

    def is_active(self) -> bool:
        """True while the session has not been completed or failed."""
        return self.completed_at is None and self.error is None

    def record_usage(self, usage: TokenUsage) -> None:
        """Replace cumulative usage; callers aggregate across turns externally."""
        self.usage = usage

    def complete(self, *, usage: TokenUsage | None = None) -> None:
        """Mark the session completed; emits AgentSessionCompleted."""
        if not self.is_active():
            raise ValueError("AgentSession is already terminal.")
        if usage is not None:
            self.usage = usage
        self.completed_at = datetime.now(timezone.utc)
        self.collect_event(
            AgentSessionCompleted(
                session_id=self.id, run_id=self.run_id, usage=self.usage
            )
        )

    def fail(self, error: str) -> None:
        """Mark the session failed; emits AgentSessionFailed."""
        if not self.is_active():
            raise ValueError("AgentSession is already terminal.")
        if not error.strip():
            raise ValueError("AgentSession failure error must not be blank.")
        self.error = error
        self.completed_at = datetime.now(timezone.utc)
        self.collect_event(
            AgentSessionFailed(
                session_id=self.id, run_id=self.run_id, error=error
            )
        )

    @classmethod
    def create(cls, *, run_id: UUID, model: str) -> "AgentSession":
        """Factory — validates model and emits AgentSessionStarted."""
        if not model.strip():
            raise ValueError("Model identifier must not be blank.")
        session = cls(run_id=run_id, model=model)
        session.collect_event(
            AgentSessionStarted(
                session_id=session.id, run_id=run_id, model=model
            )
        )
        return session
