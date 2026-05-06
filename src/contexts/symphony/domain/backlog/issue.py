"""Issue value object — immutable representation of a backlog tracker issue."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class IssuePriority(IntEnum):
    """Numeric priority levels matching Linear / common trackers."""

    NO_PRIORITY = 0
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass(frozen=True)
class Issue:
    """Immutable snapshot of a backlog tracker issue."""

    identifier: str
    title: str
    description: str
    priority: IssuePriority
    state: str
    branch_name: str | None
    labels: tuple[str, ...]
    created_at: datetime
    url: str | None = None
    updated_at: datetime | None = None
    blocked_by: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("Issue identifier must not be blank.")
        if not self.title.strip():
            raise ValueError("Issue title must not be blank.")
