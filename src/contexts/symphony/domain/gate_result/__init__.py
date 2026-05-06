"""GateResult VO — persisted record of one gate execution against a Run."""

from src.contexts.symphony.domain.gate_result.events import GateOutcomeRecorded
from src.contexts.symphony.domain.gate_result.value_object import GateResult

__all__ = ["GateOutcomeRecorded", "GateResult"]
