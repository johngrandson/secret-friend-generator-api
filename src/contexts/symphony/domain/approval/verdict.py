"""ApprovalVerdict — value object for pre-resolved approval decisions.

The HTTP layer (or any future approval channel) packages the operator's
decision into this VO and hands it to the use case. Use cases never call
back into the HTTP/UI layer — the verdict comes in already-decided.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

ApprovalDecision = Literal["ACCEPT", "REJECT"]


@dataclass(frozen=True)
class ApprovalVerdict:
    """Pre-resolved operator decision on an approval gate."""

    decision: ApprovalDecision
    approver_id: str
    timestamp: datetime
    comment: str | None = None

    def __post_init__(self) -> None:
        if self.decision not in ("ACCEPT", "REJECT"):
            raise ValueError(
                f"decision must be 'ACCEPT' or 'REJECT'; got {self.decision!r}"
            )
        if not self.approver_id.strip():
            raise ValueError("approver_id must not be blank.")

    def is_accepted(self) -> bool:
        """True iff decision == 'ACCEPT'."""
        return self.decision == "ACCEPT"
