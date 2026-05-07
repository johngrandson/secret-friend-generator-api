"""Gate ABC + GateRunner — kernel quality-gate primitive.

A ``Gate`` is one quality check that runs after the agent finishes editing.
``GateRunner`` runs gates sequentially and short-circuits on the first
blocking failure: subsequent gates emit ``SKIPPED`` outcomes so callers
get a complete record without spending CI minutes on doomed gates.

Concrete gates live in adapter packages (e.g., ``CIGate`` in
``src.contexts.symphony.adapters``). The ``ConfigT`` TypeVar lets each
concrete gate declare its own typed config without the kernel knowing
anything about Pydantic schemas.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Generic, NewType, TypeVar

log = logging.getLogger(__name__)

GateName = NewType("GateName", str)
"""Extensible gate identifier — verticals declare their own values.

Examples: ``GateName("ci")``, ``GateName("coverage")``, ``GateName("dataset_diff")``.
"""


class GateStatus(str, Enum):
    """Outcome of a single gate execution."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class GateOutcome:
    """Result of one gate execution."""

    name: GateName
    status: GateStatus
    output: str = ""
    metadata_json: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")


ConfigT = TypeVar("ConfigT")


class Gate(ABC, Generic[ConfigT]):
    """One quality gate executed against a workspace.

    Subclasses declare ``name`` and ``is_blocking`` as ``ClassVar`` and
    implement ``run``. Gates are stateless beyond their constructor config
    (timeouts, model selection, etc.).
    """

    name: ClassVar[GateName]
    is_blocking: ClassVar[bool]

    @abstractmethod
    async def run(self, *, workspace: Path, config: ConfigT) -> GateOutcome: ...


class GateRunner:
    """Runs a list of gates and aggregates outcomes.

    Sequential execution; first blocking failure causes subsequent gates
    to emit ``GateStatus.SKIPPED`` outcomes. Non-blocking failures do not
    short-circuit. Exceptions raised by ``gate.run`` are caught and
    surfaced as ``FAILED`` outcomes so a buggy gate does not poison the
    whole harness.
    """

    def __init__(self, gates: list[Gate[Any]]) -> None:
        self._gates: list[Gate[Any]] = list(gates)

    def is_blocking(self, name: GateName) -> bool:
        """Return True if a gate by ``name`` is configured as blocking."""
        for gate in self._gates:
            if gate.name == name:
                return gate.is_blocking
        return False

    async def run_all(self, *, workspace: Path, config: Any) -> list[GateOutcome]:
        outcomes: list[GateOutcome] = []
        blocked_by: str | None = None

        for gate in self._gates:
            if blocked_by is not None:
                outcomes.append(
                    GateOutcome(
                        name=gate.name,
                        status=GateStatus.SKIPPED,
                        output="",
                        metadata_json={"skipped_due_to": blocked_by},
                        duration_ms=0,
                    )
                )
                continue

            try:
                outcome = await gate.run(workspace=workspace, config=config)
            except Exception as err:
                log.warning("gate_raised gate=%s err=%s", gate.name, err)
                outcome = GateOutcome(
                    name=gate.name,
                    status=GateStatus.FAILED,
                    output=f"Gate {gate.name!r} raised: {err}",
                    metadata_json={"exception_type": type(err).__name__},
                    duration_ms=0,
                )

            outcomes.append(outcome)

            if gate.is_blocking and outcome.status == GateStatus.FAILED:
                blocked_by = str(gate.name)

        return outcomes
