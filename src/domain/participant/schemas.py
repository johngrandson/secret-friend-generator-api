from datetime import datetime
from enum import Enum
from typing import Any

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
    def at_least_one_field(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values or not any(v is not None for v in values.values()):
            raise ValueError("At least one field must be provided for update.")
        return values
