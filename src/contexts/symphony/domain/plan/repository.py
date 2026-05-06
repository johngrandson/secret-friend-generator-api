"""IPlanRepository — output port (Protocol) for Plan persistence (append-only)."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from src.contexts.symphony.domain.plan.entity import Plan


@runtime_checkable
class IPlanRepository(Protocol):
    """Structural interface for Plan persistence adapters. No delete — append-only."""

    async def find_by_id(self, plan_id: UUID) -> Plan | None: ...

    """Find a plan by its ID."""

    async def find_latest_for_run(self, run_id: UUID) -> Plan | None: ...

    """Find the latest plan for a run."""

    async def list_by_run(self, run_id: UUID) -> list[Plan]: ...

    """List all plans for a run."""

    async def save(self, plan: Plan) -> Plan: ...

    """Save a new plan."""

    async def update(self, plan: Plan) -> Plan: ...

    """Update an existing plan."""
