from sqlalchemy.orm import Session

from ..secret_friend.model import SecretFriend
from ..secret_friend.schema import LinkSecretFriend


class LinkSecretFriendRepository:
    @staticmethod
    def link_secret_friend(
        *, secret_friend: LinkSecretFriend, db_session: Session
    ) -> SecretFriend:
        """Persists a secret friend link"""
        try:
            existing_secret_friend = (
                db_session.query(SecretFriend)
                .filter_by(
                    gift_giver_id=secret_friend.gift_giver_id,
                )
                .first()
            )

            if existing_secret_friend:
                for key, value in secret_friend.model_dump(exclude_unset=True).items():
                    setattr(existing_secret_friend, key, value)

                if not db_session.object_session(existing_secret_friend):
                    db_session.merge(existing_secret_friend)

                db_session.commit()
                db_session.refresh(existing_secret_friend)
                return existing_secret_friend
            else:
                new_secret_friend = SecretFriend(
                    **secret_friend.model_dump(exclude_unset=True)
                )
                db_session.add(new_secret_friend)
                db_session.commit()
                db_session.refresh(new_secret_friend)
                return new_secret_friend

        except Exception as e:
            db_session.rollback()

            print(f"Integrity error during secret friend link: {str(e)}")
            raise ValueError(
                "Secret friend link failed. Ensure unique constraints are met."
            )
