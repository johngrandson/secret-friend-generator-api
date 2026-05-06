"""Domain events for the GateResult VO."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.agentic.gate import GateName, GateStatus
from src.shared.events import DomainEvent


@dataclass(frozen=True)
class GateOutcomeRecorded(DomainEvent):
    """Raised when a GateResult is persisted against a Run."""

    run_id: UUID
    gate_result_id: UUID
    gate_name: GateName
    status: GateStatus
