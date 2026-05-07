"""Structural contracts (Protocols) shared across orchestration handlers.

Lives outside ``dtos.py`` because these are behavioural contracts, not data.
Consumers: ``handlers/`` modules and ``run_persistence_service``.
"""

from typing import Protocol


class SubResult(Protocol):
    """Minimal protocol satisfied by every sub-use-case response dataclass.

    Allows the dispatch loop to handle ``success`` + ``error_message``
    uniformly without importing all response types into a union.
    """

    success: bool
    error_message: str | None


class Verdictable(Protocol):
    """Anything that exposes a ``verdict()`` returning approved/rejected/pending.

    Satisfied by domain ``Spec`` and ``Plan`` aggregates. Used by
    ``VerdictCheckHandlers`` to consume both via the same code path.
    """

    def verdict(self) -> str: ...
