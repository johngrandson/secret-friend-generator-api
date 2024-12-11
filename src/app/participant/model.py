from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Integer,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship
from enum import Enum

from ..database import Base


class StatusEnum(str, Enum):
    """
    Enum representing the status of a participant.
    """

    PENDING = "PENDING"
    REVEALED = "REVEALED"


class Participant(Base):
    """
    Represents a participant entity in the database.

    Attributes:
        id (int): Primary key.
        name (str): Name of the participant.
        gift_hint (str): A hint for the gift, if any.
        status (StatusEnum): Status of the participant (e.g., PENDING, REVEALED).
        created_at (datetime): Timestamp when the participant was created.
        updated_at (datetime): Timestamp when the participant was last updated.
        group_id (int): Foreign key referencing the associated group.
        group (Group): Relationship to the associated group.
        gift_giver (SecretFriend): Relationship to the secret friend assigned as the gift giver.
        gift_receiver (SecretFriend): Relationship to the secret friend assigned as the gift receiver.
    """

    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    gift_hint = Column(String, nullable=True)
    status = Column(
        SQLAlchemyEnum(StatusEnum), nullable=False, default=StatusEnum.PENDING
    )
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    group = relationship("Group", back_populates="participants")

    gift_giver = relationship(
        "SecretFriend",
        foreign_keys="SecretFriend.gift_giver_id",
        back_populates="giver",
        uselist=False,
        cascade="all, delete-orphan",
    )

    gift_receiver = relationship(
        "SecretFriend",
        foreign_keys="SecretFriend.gift_receiver_id",
        back_populates="receiver",
        uselist=False,
        cascade="all, delete-orphan",
    )
