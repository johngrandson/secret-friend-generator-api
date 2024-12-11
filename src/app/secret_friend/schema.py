from pydantic import BaseModel, Field, model_validator


class LinkSecretFriend(BaseModel):
    """
    Schema for linking a secret friend relationship between a gift giver and a gift receiver.
    """
    gift_giver_id: int = Field(..., gt=0, description="ID of the gift giver (must be a positive integer).")
    gift_receiver_id: int = Field(..., gt=0, description="ID of the gift receiver (must be a positive integer).")

    @model_validator(mode="before")
    @classmethod
    def validate_ids_are_distinct(cls, data):
        """
        Ensure that the gift giver and gift receiver are not the same person.
        """
        gift_giver_id = data.get("gift_giver_id")
        gift_receiver_id = data.get("gift_receiver_id")

        if gift_giver_id is not None and gift_giver_id == gift_receiver_id:
            raise ValueError("Gift giver and gift receiver cannot be the same person.")
        return data
