from sqlalchemy.orm import Session

from src.domain.group.repository import GroupRepository
from src.domain.group.schemas import GroupCreate, GroupList, GroupRead


class GroupService:
    @staticmethod
    def create(group: GroupCreate, db_session: Session) -> GroupRead:
        result = GroupRepository.create(group=group, db_session=db_session)
        return GroupRead.model_validate(result)

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
