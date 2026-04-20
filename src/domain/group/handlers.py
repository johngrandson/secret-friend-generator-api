"""Group lifecycle handlers."""
import logging
from typing import Any

from src.domain.group.signals import group_created, group_deleted, group_updated
from src.shared.signals import isolated
from src.shared.task_backend import dispatch_task

log = logging.getLogger(__name__)


# ── Side-effect handlers ─────────────────────────────────────────────────────

@isolated
def _on_group_created(sender: type, *, group: Any, **_: Any) -> None:
    log.info("lifecycle: group created — id=%s name=%s", group.id, group.name)


@isolated
def _on_group_updated(sender: type, *, group: Any, **_: Any) -> None:
    log.info("lifecycle: group updated — id=%s name=%s", group.id, group.name)


@isolated
def _on_group_deleted(sender: type, *, group_id: int, **_: Any) -> None:
    log.info("lifecycle: group deleted — id=%s", group_id)


# ── Task relays (bridge to background task queue) ────────────────────────────

@isolated
def _relay_group_created(sender: type, *, group: Any, **_: Any) -> None:
    dispatch_task("notifications.group_created", group_id=group.id, group_name=group.name)


@isolated
def _relay_group_updated(sender: type, *, group: Any, **_: Any) -> None:
    dispatch_task("notifications.group_updated", group_id=group.id, group_name=group.name)


@isolated
def _relay_group_deleted(sender: type, *, group_id: int, **_: Any) -> None:
    dispatch_task("notifications.group_deleted", group_id=group_id)


# ── Registration ─────────────────────────────────────────────────────────────

def register() -> None:
    """Connect group lifecycle handlers to their signals."""
    group_created.connect(_on_group_created)
    group_created.connect(_relay_group_created)
    group_updated.connect(_on_group_updated)
    group_updated.connect(_relay_group_updated)
    group_deleted.connect(_on_group_deleted)
    group_deleted.connect(_relay_group_deleted)
