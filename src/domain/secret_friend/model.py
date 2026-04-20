from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence import Base


class SecretFriend(Base):
    __tablename__ = "secret_friends"
    __table_args__ = (
        UniqueConstraint(
            "gift_giver_id", "gift_receiver_id", name="uq_gift_giver_receiver"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    gift_giver_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), nullable=False)
    giver: Mapped[Optional["Participant"]] = relationship(
        foreign_keys=[gift_giver_id],
        back_populates="gift_giver",
    )

    gift_receiver_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), nullable=False, index=True)
    receiver: Mapped[Optional["Participant"]] = relationship(
        foreign_keys=[gift_receiver_id],
        back_populates="gift_receiver",
    )
