"""Tests for group domain signal emission via GroupService."""

from sqlalchemy.orm import Session

from src.domain.group.schemas import GroupCreate, GroupUpdate
from src.domain.group.service import GroupService
from src.domain.group.signals import group_created, group_deleted, group_updated


def test_group_created_signal_fires_on_create(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kwargs: object) -> None:
        received.append(kwargs)

    group_created.connect(handler)
    try:
        GroupService.create(GroupCreate(name="Signal Group", description="desc"), db_session)
        assert len(received) == 1
        assert received[0]["group"].name == "Signal Group"
    finally:
        group_created.disconnect(handler)


def test_group_updated_signal_fires_on_update(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kwargs: object) -> None:
        received.append(kwargs)

    group = GroupService.create(GroupCreate(name="Before Update", description="d"), db_session)

    group_updated.connect(handler)
    try:
        GroupService.update(group.id, GroupUpdate(name="After Update"), db_session)
        assert len(received) == 1
        assert received[0]["group"].name == "After Update"
    finally:
        group_updated.disconnect(handler)


def test_group_deleted_signal_fires_on_delete(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kwargs: object) -> None:
        received.append(kwargs)

    group = GroupService.create(GroupCreate(name="To Delete", description="d"), db_session)

    group_deleted.connect(handler)
    try:
        GroupService.delete(group.id, db_session)
        assert len(received) == 1
        assert received[0]["group_id"] == group.id
    finally:
        group_deleted.disconnect(handler)
