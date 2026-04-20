from typing import Any

from pydantic import BaseModel, Field, model_validator


class SecretFriendLink(BaseModel):
    gift_giver_id: int = Field(..., gt=0)
    gift_receiver_id: int = Field(..., gt=0)

    @model_validator(mode="before")
    @classmethod
    def validate_ids_are_distinct(cls, data: dict[str, Any]) -> dict[str, Any]:
        gift_giver_id = data.get("gift_giver_id")
        gift_receiver_id = data.get("gift_receiver_id")
        if gift_giver_id is not None and gift_giver_id == gift_receiver_id:
            raise ValueError("Gift giver and gift receiver cannot be the same person.")
        return data


class SecretFriendRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    gift_giver_id: int
    gift_receiver_id: int
