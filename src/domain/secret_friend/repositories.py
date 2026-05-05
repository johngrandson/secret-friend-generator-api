"""SecretFriend output port — repository Protocol (driven side of hexagon)."""

from typing import Protocol

from src.domain.secret_friend.entities import SecretFriend


class ISecretFriendRepository(Protocol):
    def link(self, secret_friend: SecretFriend) -> SecretFriend: ...
    def get_by_id(self, secret_friend_id: int) -> SecretFriend: ...
    def delete(self, secret_friend_id: int) -> None: ...
