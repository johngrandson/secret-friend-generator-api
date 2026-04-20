from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.shared.database_base import Base
from src.domain.group.schemas import CategoryEnum


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    link_url: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    category: Mapped[CategoryEnum] = mapped_column(
        SQLAlchemyEnum(CategoryEnum), nullable=False, default=CategoryEnum.santa
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc)
    )

    participants: Mapped[list["Participant"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
