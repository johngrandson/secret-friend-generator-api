from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

from ..database import Base


class SecretFriend(Base):
    """
    Represents a secret friend assignment in the database.

    Attributes:
        id (int): Primary key.
        created_at (datetime): Timestamp when the record was created.
        gift_giver_id (int): Foreign key referencing the participant assigned as the gift giver.
        gift_receiver_id (int): Foreign key referencing the participant assigned as the gift receiver.
        giver (Participant): Relationship to the gift giver participant.
        receiver (Participant): Relationship to the gift receiver participant.
    """

    __tablename__ = "secret_friends"
    __table_args__ = (
        UniqueConstraint(
            "gift_giver_id", "gift_receiver_id", name="uq_gift_giver_receiver"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default="CURRENT_TIMESTAMP",
    )

    gift_giver_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    giver = relationship(
        "Participant",
        foreign_keys=[gift_giver_id],
        back_populates="gift_giver",
    )

    gift_receiver_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    receiver = relationship(
        "Participant",
        foreign_keys=[gift_receiver_id],
        back_populates="gift_receiver",
    )
