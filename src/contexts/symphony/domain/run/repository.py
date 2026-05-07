"""IRunRepository — output port (Protocol) for Run persistence."""

import builtins
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.contexts.symphony.domain.run.entity import Run


@runtime_checkable
class IRunRepository(Protocol):
    """Structural interface for Run persistence adapters."""

    async def find_by_id(self, run_id: UUID) -> Run | None: ...

    """Find a run by its ID."""

    async def find_due_retries(self, now: datetime) -> builtins.list[Run]: ...

    """Find runs that are due for retry."""

    async def count_active(self) -> int: ...

    """Count runs whose status is not terminal (DONE / FAILED)."""

    async def list_active_identifiers(self) -> builtins.list[str]: ...

    """Return ``issue_id`` values for all non-terminal runs (dedup helper)."""

    async def list(self, limit: int = 20, offset: int = 0) -> builtins.list[Run]: ...

    """List runs with pagination."""

    async def save(self, run: Run) -> Run: ...

    """Save a new run."""

    async def update(self, run: Run) -> Run: ...

    """Update an existing run."""

    async def delete(self, run_id: UUID) -> bool: ...

    """Delete a run by its ID."""
