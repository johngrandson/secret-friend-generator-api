from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.secret_friend.secret_friend_model import SecretFriend
from src.domain.secret_friend.secret_friend_schemas import SecretFriendLink
from src.domain.shared.domain_exceptions import ConflictError


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
                db_session.rollback()
                raise ConflictError("Secret friend link update failed.")
            return existing

        new_sf = SecretFriend(**secret_friend.model_dump())
        try:
            db_session.add(new_sf)
            db_session.flush()
            db_session.refresh(new_sf)
        except IntegrityError:
            db_session.rollback()
            raise ConflictError("Secret friend link failed. Unique constraint violated.")
        return new_sf
