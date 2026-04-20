"""Group notification handlers — pure business logic, no infrastructure deps."""
import logging

log = logging.getLogger(__name__)


def on_group_created(*, group_id: int, group_name: str) -> None:
    """Handle group-created notification."""
    log.info("notification: group created — id=%s name=%s", group_id, group_name)


def on_group_updated(*, group_id: int, group_name: str) -> None:
    """Handle group-updated notification."""
    log.info("notification: group updated — id=%s name=%s", group_id, group_name)


def on_group_deleted(*, group_id: int) -> None:
    """Handle group-deleted notification."""
    log.info("notification: group deleted — id=%s", group_id)
