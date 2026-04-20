from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.secret_friend.model import SecretFriend
from src.domain.secret_friend.schemas import SecretFriendLink
from src.shared.exceptions import ConflictError, NotFoundError


class SecretFriendRepository:
    @staticmethod
    def link(secret_friend: SecretFriendLink, db_session: Session) -> SecretFriend:
        """Creates or updates a secret friend link (upsert by gift_giver_id)."""
        stmt = select(SecretFriend).where(
            SecretFriend.gift_giver_id == secret_friend.gift_giver_id
        )
        existing = db_session.execute(stmt).scalars().one_or_none()

        if existing:
            existing.gift_receiver_id = secret_friend.gift_receiver_id
            try:
                db_session.flush()
                db_session.refresh(existing)
            except IntegrityError:
                raise ConflictError("Secret friend link update failed.")
            return existing

        new_sf = SecretFriend(**secret_friend.model_dump())
        try:
            db_session.add(new_sf)
            db_session.flush()
            db_session.refresh(new_sf)
        except IntegrityError:
            raise ConflictError("Secret friend link failed. Unique constraint violated.")
        return new_sf

    @staticmethod
    def get_by_id(secret_friend_id: int, db_session: Session) -> SecretFriend:
        secret_friend = db_session.get(SecretFriend, secret_friend_id)
        if not secret_friend:
            raise NotFoundError("Secret friend assignment not found")
        return secret_friend

    @staticmethod
    def delete(secret_friend_id: int, db_session: Session) -> None:
        secret_friend = db_session.get(SecretFriend, secret_friend_id)
        if not secret_friend:
            raise NotFoundError("Secret friend assignment not found")
        db_session.delete(secret_friend)
        db_session.flush()
