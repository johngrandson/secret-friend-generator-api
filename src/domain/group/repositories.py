"""Group output port — repository Protocol (driven side of hexagon)."""

from typing import Protocol

from src.domain.group.entities import Group
from src.domain.group.value_objects import CategoryEnum


class IGroupRepository(Protocol):
    def create(self, group: Group) -> Group: ...
    def get_all(self) -> list[Group]: ...
    def get_by_id(self, group_id: int) -> Group: ...
    def get_by_link_url(self, link_url: str) -> Group: ...
    def update(
        self,
        group_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        category: CategoryEnum | None = None,
    ) -> Group: ...
    def delete(self, group_id: int) -> None: ...
