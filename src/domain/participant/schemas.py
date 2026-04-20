from datetime import datetime
from enum import Enum

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
    gift_hint: str | None = None
    status: ParticipantStatus = ParticipantStatus.PENDING
    created_at: datetime
    updated_at: datetime | None = None


class ParticipantList(BaseModel):
    participants: list[ParticipantRead]


class ParticipantUpdate(BaseModel):
    name: str | None = None
    gift_hint: str | None = None
    status: ParticipantStatus | None = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one_field(cls, data: object) -> object:
        if isinstance(data, dict) and not any(data.values()):
            raise ValueError("At least one field must be provided")
        return data
