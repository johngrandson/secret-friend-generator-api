"""Group lifecycle handlers."""
import logging
from typing import Any

from src.domain.group.signals import group_created
from src.domain.shared.signals import isolated
from src.domain.shared.task_backend import dispatch_task

log = logging.getLogger(__name__)


# ── Side-effect handlers ─────────────────────────────────────────────────────

@isolated
def _on_group_created(sender: type, *, group: Any, **_: Any) -> None:
    log.info("lifecycle: group created — id=%s name=%s", group.id, group.name)


# ── Task relays (bridge to background task queue) ────────────────────────────

@isolated
def _relay_group_created(sender: type, *, group: Any, **_: Any) -> None:
    dispatch_task("notifications.group_created", group_id=group.id, group_name=group.name)


# ── Registration ─────────────────────────────────────────────────────────────

def register() -> None:
    """Connect group lifecycle handlers to their signals."""
    group_created.connect(_on_group_created)
    group_created.connect(_relay_group_created)
