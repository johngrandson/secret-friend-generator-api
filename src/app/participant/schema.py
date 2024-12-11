from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class PydanticBaseModel(BaseModel):
    """
    Base Pydantic model with common configuration for all schemas.
    """

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


# Enum for Participant Status
class StatusEnum(str, Enum):
    PENDING = "PENDING"
    REVEALED = "REVEALED"


# Base schema for Participants
class ParticipantBase(PydanticBaseModel):
    """
    Base schema for Participant containing shared fields.
    """

    id: int
    name: str


# Schema for creating a Participant
class ParticipantCreate(ParticipantBase):
    """
    Schema for creating a new Participant.
    """
    group_id: int


# Schema for reading a Participant
class ParticipantRead(ParticipantBase):
    """
    Schema for reading a Participant with additional metadata.
    """

    gift_hint: Optional[str] = None
    status: StatusEnum = StatusEnum.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


# Schema for a list of Participants
class ParticipantsRead(PydanticBaseModel):
    """
    Schema for reading a list of Participants.
    """

    participants: List[ParticipantRead]


# Schema for updating a Participant
class ParticipantUpdate(PydanticBaseModel):
    """
    Schema for updating a Participant. At least one field must be provided.
    """

    name: Optional[str] = None
    gift_hint: Optional[str] = None
    status: Optional[StatusEnum] = None

    @model_validator(mode="before")
    def at_least_one_field(cls, values):
        """
        Ensure that at least one field is provided for the update.
        """
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update.")
        return values
