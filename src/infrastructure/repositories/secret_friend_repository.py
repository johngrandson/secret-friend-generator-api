"""Postgres adapter for ISecretFriendRepository — maps ORM ↔ SecretFriend entity."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.secret_friend.entities import SecretFriend
from src.infrastructure.persistence.models import SecretFriendORM
from src.shared.exceptions import ConflictError, NotFoundError


def _to_entity(orm: SecretFriendORM) -> SecretFriend:
    return SecretFriend(
        id=orm.id,
        gift_giver_id=orm.gift_giver_id,
        gift_receiver_id=orm.gift_receiver_id,
        created_at=orm.created_at,
    )


class PostgresSecretFriendRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def link(self, secret_friend: SecretFriend) -> SecretFriend:
        stmt = select(SecretFriendORM).where(
            SecretFriendORM.gift_giver_id == secret_friend.gift_giver_id
        )
        existing = self._db.execute(stmt).scalars().one_or_none()
        if existing is not None:
            existing.gift_receiver_id = secret_friend.gift_receiver_id
            try:
                self._db.flush()
                self._db.refresh(existing)
            except IntegrityError as exc:
                raise ConflictError(
                    "Secret friend link update failed."
                ) from exc
            return _to_entity(existing)

        orm = SecretFriendORM(
            gift_giver_id=secret_friend.gift_giver_id,
            gift_receiver_id=secret_friend.gift_receiver_id,
        )
        try:
            self._db.add(orm)
            self._db.flush()
            self._db.refresh(orm)
        except IntegrityError as exc:
            raise ConflictError(
                "Secret friend link failed. Unique constraint violated."
            ) from exc
        return _to_entity(orm)

    def get_by_id(self, secret_friend_id: int) -> SecretFriend:
        orm = self._db.get(SecretFriendORM, secret_friend_id)
        if orm is None:
            raise NotFoundError("Secret friend assignment not found")
        return _to_entity(orm)

    def delete(self, secret_friend_id: int) -> None:
        orm = self._db.get(SecretFriendORM, secret_friend_id)
        if orm is None:
            raise NotFoundError("Secret friend assignment not found")
        self._db.delete(orm)
        self._db.flush()
