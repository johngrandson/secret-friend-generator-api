"""Group side-effect handlers — @isolated, errors are swallowed."""

import logging

from src.domain.group.schemas import GroupRead
from src.domain.group.signals import group_created, group_deleted, group_updated
from src.shared.signals import isolated

log = logging.getLogger(__name__)


@isolated
def _on_group_created(sender: type, *, group: GroupRead, **kwargs: object) -> None:
    log.info("lifecycle: group created — id=%s name=%s", group.id, group.name)


@isolated
def _on_group_updated(sender: type, *, group: GroupRead, **kwargs: object) -> None:
    log.info("lifecycle: group updated — id=%s name=%s", group.id, group.name)


@isolated
def _on_group_deleted(sender: type, *, group_id: int, **kwargs: object) -> None:
    log.info("lifecycle: group deleted — id=%s", group_id)


def register_side_effects() -> None:
    """Connect group side-effect handlers to their signals."""
    group_created.connect(_on_group_created)
    group_updated.connect(_on_group_updated)
    group_deleted.connect(_on_group_deleted)
