"""IAgentSessionRepository — output port (Protocol) for AgentSession persistence."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from src.contexts.symphony.domain.agent_session.entity import AgentSession


@runtime_checkable
class IAgentSessionRepository(Protocol):
    """Structural interface for AgentSession persistence adapters."""

    async def find_by_id(self, session_id: UUID) -> AgentSession | None: ...

    async def find_active_for_run(self, run_id: UUID) -> AgentSession | None: ...

    async def list_by_run(self, run_id: UUID) -> list[AgentSession]: ...

    async def save(self, session: AgentSession) -> AgentSession: ...

    async def update(self, session: AgentSession) -> AgentSession: ...
