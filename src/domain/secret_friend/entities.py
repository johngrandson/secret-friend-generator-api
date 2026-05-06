"""SecretFriend aggregate — invariant enforced on creation, not on hydration."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SecretFriend:
    gift_giver_id: int
    gift_receiver_id: int
    id: int | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def create(
        cls, *, gift_giver_id: int, gift_receiver_id: int
    ) -> "SecretFriend":
        """Factory that enforces the giver != receiver invariant.

        Use this for new assignments. Hydration paths (e.g. repo mappers
        rebuilding a row from the database) construct via the bare
        constructor so corrupt rows surface as data errors, not validation
        500s on read.
        """
        if gift_giver_id == gift_receiver_id:
            raise ValueError(
                "Gift giver and gift receiver cannot be the same person."
            )
        return cls(
            gift_giver_id=gift_giver_id, gift_receiver_id=gift_receiver_id
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SecretFriend):
            return False
        return self.id is not None and self.id == other.id

    def __hash__(self) -> int:
        return hash(("SecretFriend", self.id))
