"""IGateResultRepository — output port for GateResult persistence (append-only)."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from src.contexts.symphony.domain.gate_result.value_object import GateResult


@runtime_checkable
class IGateResultRepository(Protocol):
    """Structural interface for GateResult persistence adapters."""

    async def save_batch(self, results: list[GateResult]) -> list[GateResult]: ...

    """Persist all gate results in a batch; returns the saved values."""

    async def find_by_run(self, run_id: UUID) -> list[GateResult]: ...

    """Return all gate results for a Run, ordered by created_at ascending."""
