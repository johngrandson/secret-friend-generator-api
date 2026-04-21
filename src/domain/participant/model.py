from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence import Base
from src.domain.participant.schemas import ParticipantStatus


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    gift_hint: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[ParticipantStatus] = mapped_column(
        SQLAlchemyEnum(ParticipantStatus),
        nullable=False,
        default=ParticipantStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc),
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), nullable=False, index=True
    )
    group: Mapped["Group"] = relationship(back_populates="participants")

    gift_giver: Mapped["SecretFriend | None"] = relationship(
        foreign_keys="SecretFriend.gift_giver_id",
        back_populates="giver",
        uselist=False,
        cascade="all, delete-orphan",
    )
    gift_receiver: Mapped["SecretFriend | None"] = relationship(
        foreign_keys="SecretFriend.gift_receiver_id",
        back_populates="receiver",
        uselist=False,
        cascade="all, delete",
        passive_deletes=True,
    )
