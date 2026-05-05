"""Group use cases — depend on Protocol, operate on domain entities."""

from sqlalchemy.orm import Session

from src.domain.group.entities import Group
from src.domain.group.repositories import IGroupRepository
from src.domain.group.signals import group_created, group_deleted, group_updated
from src.domain.group.value_objects import CategoryEnum
from src.infrastructure.persistence import transaction
from src.shared.hashing import generate_group_token


class GroupService:
    def __init__(self, repo: IGroupRepository, db: Session) -> None:
        self._repo = repo
        self._db = db

    def create(
        self,
        *,
        name: str,
        description: str,
        category: CategoryEnum = CategoryEnum.santa,
    ) -> Group:
        with transaction(self._db):
            entity = self._repo.create(
                Group(
                    name=name,
                    description=description,
                    category=category,
                    link_url=generate_group_token(),
                )
            )
            group_created.send(self.__class__, group=entity)
            return entity

    def get_all(self) -> list[Group]:
        return self._repo.get_all()

    def get_by_id(self, group_id: int) -> Group:
        return self._repo.get_by_id(group_id)

    def get_by_link_url(self, link_url: str) -> Group:
        return self._repo.get_by_link_url(link_url)

    def update(
        self,
        group_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        category: CategoryEnum | None = None,
    ) -> Group:
        fields = {
            k: v
            for k, v in {
                "name": name,
                "description": description,
                "category": category,
            }.items()
            if v is not None
        }
        with transaction(self._db):
            entity = self._repo.update(group_id, **fields)
            group_updated.send(self.__class__, group=entity)
            return entity

    def delete(self, group_id: int) -> None:
        with transaction(self._db):
            self._repo.delete(group_id)
            group_deleted.send(self.__class__, group_id=group_id)
