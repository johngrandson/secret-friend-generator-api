"""Postgres adapter for IGroupRepository — maps ORM ↔ Group entity."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.group.entities import Group
from src.domain.group.value_objects import ParticipantSummary
from src.infrastructure.persistence.models import GroupORM
from src.shared.exceptions import ConflictError, NotFoundError


def _to_entity(orm: GroupORM) -> Group:
    return Group(
        id=orm.id,
        name=orm.name,
        description=orm.description,
        link_url=orm.link_url,
        category=orm.category,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        participants=[
            ParticipantSummary(id=p.id, name=p.name) for p in orm.participants
        ],
    )


class PostgresGroupRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, group: Group) -> Group:
        orm = GroupORM(
            name=group.name,
            description=group.description,
            category=group.category,
            link_url=group.link_url,
        )
        try:
            self._db.add(orm)
            self._db.flush()
            self._db.refresh(orm)
        except IntegrityError as exc:
            raise ConflictError(
                "Group creation failed. Unique constraint violated."
            ) from exc
        return _to_entity(orm)

    def get_all(self) -> list[Group]:
        rows = self._db.execute(select(GroupORM)).scalars().all()
        return [_to_entity(g) for g in rows]

    def get_by_id(self, group_id: int) -> Group:
        orm = self._db.get(GroupORM, group_id)
        if orm is None:
            raise NotFoundError("Group not found")
        return _to_entity(orm)

    def get_by_link_url(self, link_url: str) -> Group:
        stmt = select(GroupORM).where(GroupORM.link_url == link_url)
        orm = self._db.execute(stmt).scalars().one_or_none()
        if orm is None:
            raise NotFoundError("Group not found")
        return _to_entity(orm)

    def update(self, group_id: int, **fields: Any) -> Group:
        orm = self._db.get(GroupORM, group_id)
        if orm is None:
            raise NotFoundError("Group not found")
        for key, value in fields.items():
            setattr(orm, key, value)
        try:
            self._db.flush()
            self._db.refresh(orm)
        except IntegrityError as exc:
            raise ConflictError(
                "Group update failed. Unique constraint violated."
            ) from exc
        return _to_entity(orm)

    def delete(self, group_id: int) -> None:
        orm = self._db.get(GroupORM, group_id)
        if orm is None:
            raise NotFoundError("Group not found")
        self._db.delete(orm)
        self._db.flush()
