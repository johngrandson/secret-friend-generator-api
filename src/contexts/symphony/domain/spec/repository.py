"""ISpecRepository — output port (Protocol) for Spec persistence (append-only)."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from src.contexts.symphony.domain.spec.entity import Spec


@runtime_checkable
class ISpecRepository(Protocol):
    """Structural interface for Spec persistence adapters. No delete — append-only."""

    async def find_by_id(self, spec_id: UUID) -> Spec | None: ...

    """Find a spec by its ID."""

    async def find_latest_for_run(self, run_id: UUID) -> Spec | None: ...

    """Find the latest spec for a run."""

    async def list_by_run(self, run_id: UUID) -> list[Spec]: ...

    """List all specs for a run."""

    async def save(self, spec: Spec) -> Spec: ...

    """Save a new spec."""

    async def update(self, spec: Spec) -> Spec: ...

    """Update an existing spec."""
