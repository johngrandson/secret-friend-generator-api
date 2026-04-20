"""Secret friend lifecycle handlers."""
import logging

from src.domain.secret_friend.signals import secret_friend_assigned
from src.domain.shared.signals import isolated
from src.domain.shared.task_backend import dispatch_task

log = logging.getLogger(__name__)


# ── Side-effect handlers ─────────────────────────────────────────────────────

@isolated
def _on_secret_friend_assigned(sender, *, assignment, group_id, **_):
    log.info(
        "lifecycle: secret friend assigned — id=%s group_id=%s",
        assignment.id,
        group_id,
    )


# ── Task relays (bridge to background task queue) ────────────────────────────

@isolated
def _relay_secret_friend_assigned(sender, *, assignment, group_id, **_):
    dispatch_task(
        "notifications.secret_friend_assigned",
        assignment_id=assignment.id,
        group_id=group_id,
    )


# ── Registration ─────────────────────────────────────────────────────────────

def register() -> None:
    """Connect secret friend lifecycle handlers to their signals."""
    secret_friend_assigned.connect(_on_secret_friend_assigned)
    secret_friend_assigned.connect(_relay_secret_friend_assigned)
