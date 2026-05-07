"""IAgentSessionRepository — output port (Protocol) for AgentSession persistence."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from src.contexts.symphony.domain.agent_session.entity import AgentSession


@runtime_checkable
class IAgentSessionRepository(Protocol):
    """Structural interface for AgentSession persistence adapters."""

    async def find_by_id(self, session_id: UUID) -> AgentSession | None: ...

    """Find a session by its ID."""

    async def find_active_for_run(self, run_id: UUID) -> AgentSession | None: ...

    """Find the active (non-completed) session for a given run."""

    async def list_by_run(self, run_id: UUID) -> list[AgentSession]: ...

    """List all sessions for a given run, ordered by creation time."""

    async def save(self, session: AgentSession) -> AgentSession: ...

    """Save a new session to the repository."""

    async def update(self, session: AgentSession) -> AgentSession: ...

    """Update an existing session in the repository."""

    async def delete(self, session_id: UUID) -> bool: ...

    """Delete a session by its ID."""
