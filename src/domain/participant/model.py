from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.shared.database_base import Base
from src.domain.participant.schemas import ParticipantStatus


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    gift_hint: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[ParticipantStatus] = mapped_column(
        SQLAlchemyEnum(ParticipantStatus), nullable=False, default=ParticipantStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, onupdate=lambda: datetime.now(timezone.utc)
    )

    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    group: Mapped["Group"] = relationship(back_populates="participants")

    gift_giver: Mapped[Optional["SecretFriend"]] = relationship(
        foreign_keys="SecretFriend.gift_giver_id",
        back_populates="giver",
        uselist=False,
        cascade="all, delete-orphan",
    )
    gift_receiver: Mapped[Optional["SecretFriend"]] = relationship(
        foreign_keys="SecretFriend.gift_receiver_id",
        back_populates="receiver",
        uselist=False,
        cascade="all, delete-orphan",
    )
