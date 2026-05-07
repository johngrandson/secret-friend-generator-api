"""SQLAlchemy 2.0 ORM models for the Organization aggregate.

Two tables back the aggregate:

- `organizations` — root row (id, name, slug).
- `organization_members` — junction (organization_id, user_id, role) with
  composite primary key. The aggregate root owns its membership rows;
  ON DELETE CASCADE keeps the relational invariant.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.adapters.persistence.base import Base


class OrganizationModel(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class OrganizationMemberModel(Base):
    __tablename__ = "organization_members"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(primary_key=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
