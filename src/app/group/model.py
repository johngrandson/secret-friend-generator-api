from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from ..database import Base
from ..group.schema import CategoryEnum


class Group(Base):
    """
    Represents a Group entity in the database.

    Attributes:
        id (int): Primary key.
        name (str): Name of the group.
        description (str): Description of the group.
        link_url (str): Unique URL link for the group.
        category (CategoryEnum): Category of the group.
        created_at (datetime): Timestamp when the group was created.
        updated_at (datetime): Timestamp when the group was last updated.
        participants (list): List of participants associated with the group.
    """

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    link_url = Column(String, nullable=True, unique=True)
    category = Column(
        SQLAlchemyEnum(CategoryEnum), nullable=False, default=CategoryEnum.santa
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now(),
        server_default="CURRENT_TIMESTAMP",
    )
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now)

    participants = relationship(
        "Participant", back_populates="group", cascade="all, delete-orphan"
    )
