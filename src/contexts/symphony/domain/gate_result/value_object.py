"""GateResult VO — immutable persisted record of one gate execution.

Distinct from ``shared.agentic.GateOutcome``: the kernel ``GateOutcome`` is
the in-memory result the harness produces, while ``GateResult`` is the
domain VO that tracks association with a Run and bounds the output size
for safe persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.shared.agentic.gate import GateName, GateStatus

OUTPUT_MAX_LEN = 5_000


@dataclass(frozen=True)
class GateResult:
    """Persisted outcome of one gate execution against a Run."""

    run_id: UUID
    gate_name: GateName
    status: GateStatus
    output: str = ""
    duration_ms: int = 0
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")
        if len(self.output) > OUTPUT_MAX_LEN:
            object.__setattr__(self, "output", self.output[:OUTPUT_MAX_LEN])
