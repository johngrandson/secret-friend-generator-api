import uuid
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from ..participant.schema import ParticipantBase


class PydanticBaseModel(BaseModel):
    """
    Base Pydantic model with common configuration.
    """

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class CategoryEnum(str, Enum):
    """
    Enumeration of group categories.
    """

    santa = "santa"
    chocolate = "chocolate"
    frenemy = "frenemy"
    book = "book"
    wine = "wine"
    easter = "easter"


class GroupCreate(PydanticBaseModel):
    """
    Schema for creating a new Group.
    """

    name: str = Field(..., min_length=4)
    description: str
    link_url: Optional[str] = None
    category: CategoryEnum = CategoryEnum.santa

    @field_validator("link_url", mode="before")
    def generate_link_url(cls, value):
        """
        Generate a unique link if none is provided.
        """
        if not value:
            return str(uuid.uuid4())
        if not isinstance(value, str):
            raise ValueError("The link_url must be a string.")
        return value


class ShowGroup(PydanticBaseModel):
    """
    Schema for reading a Group with its details and associated Participants.
    """

    id: int
    name: str
    description: str
    category: CategoryEnum = CategoryEnum.santa
    link_url: Optional[str] = None
    participants: List[ParticipantBase]

    @classmethod
    def from_orm_with_participants(cls, group, participants=None):
        """
        Custom method to convert a Group ORM model and its participants into a ShowGroup schema.
        Handles cases where participants are None or empty.
        """
        participants = participants or []
        return cls(
            id=group.id,
            name=group.name,
            description=group.description,
            category=group.category,
            link_url=group.link_url,
            participants=[
                ParticipantBase.model_validate(participant)
                for participant in participants
            ],
        )


class ShowGroups(PydanticBaseModel):
    """
    Schema for reading multiple Groups.
    """

    groups: List[ShowGroup] = Field(default_factory=list)
