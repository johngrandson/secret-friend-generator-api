from sqlalchemy.orm import Session

from src.domain.group.repository import GroupRepository
from src.domain.group.schemas import GroupCreate, GroupList, GroupRead, GroupUpdate
from src.domain.group.signals import group_created, group_deleted, group_updated
from src.infrastructure.persistence import transaction


class GroupService:
    @staticmethod
    def create(group: GroupCreate, db_session: Session) -> GroupRead:
        with transaction(db_session):
            result = GroupRepository.create(group=group, db_session=db_session)
            validated = GroupRead.model_validate(result)
            group_created.send(GroupService, group=validated)
            return validated

    @staticmethod
    def update(group_id: int, payload: GroupUpdate, db_session: Session) -> GroupRead:
        with transaction(db_session):
            result = GroupRepository.update(
                group_id=group_id, payload=payload, db_session=db_session
            )
            validated = GroupRead.model_validate(result)
            group_updated.send(GroupService, group=validated)
            return validated

    @staticmethod
    def delete(group_id: int, db_session: Session) -> None:
        with transaction(db_session):
            GroupRepository.delete(group_id=group_id, db_session=db_session)
            group_deleted.send(GroupService, group_id=group_id)

    @staticmethod
    def get_all(db_session: Session) -> GroupList:
        groups = GroupRepository.get_all(db_session=db_session)
        items = [GroupRead.model_validate(g) for g in groups]
        return GroupList(groups=items)

    @staticmethod
    def get_by_id(group_id: int, db_session: Session) -> GroupRead:
        result = GroupRepository.get_by_id(group_id=group_id, db_session=db_session)
        return GroupRead.model_validate(result)

    @staticmethod
    def get_by_link_url(link_url: str, db_session: Session) -> GroupRead:
        result = GroupRepository.get_by_link_url(link_url=link_url, db_session=db_session)
        return GroupRead.model_validate(result)
