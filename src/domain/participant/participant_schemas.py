from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator


class ParticipantStatus(str, Enum):
    PENDING = "PENDING"
    REVEALED = "REVEALED"


class ParticipantBase(BaseModel):
    """Minimal schema used by GroupRead to avoid circular imports."""
    model_config = {"from_attributes": True}

    id: int
    name: str


class ParticipantCreate(BaseModel):
    name: str
    group_id: int


class ParticipantRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    group_id: int
    gift_hint: Optional[str] = None
    status: ParticipantStatus = ParticipantStatus.PENDING
    created_at: datetime
    updated_at: Optional[datetime] = None


class ParticipantList(BaseModel):
    model_config = {"from_attributes": True}

    participants: list[ParticipantRead]


class ParticipantUpdate(BaseModel):
    name: Optional[str] = None
    gift_hint: Optional[str] = None
    status: Optional[ParticipantStatus] = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one_field(cls, values: dict) -> dict:
        if not values:
            raise ValueError("At least one field must be provided for update.")
        return values
