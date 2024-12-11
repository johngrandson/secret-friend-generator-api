from sqlalchemy.orm import Session

from ..group.schema import GroupCreate, ShowGroup, ShowGroups
from ..group.repository import GroupRepository


class GroupService:
    @staticmethod
    def create(group: GroupCreate, db_session: Session) -> ShowGroup:
        """Business logic for creating a new group"""
        group = GroupRepository.create_new_group(group=group, db_session=db_session)
        return ShowGroup.model_validate(group)

    @staticmethod
    def get_all(db_session: Session) -> ShowGroups:
        """Business logic for getting all groups"""
        groups = GroupRepository.get_all_groups(db_session=db_session)
        return ShowGroups.model_validate(groups)

    @staticmethod
    def get_by_id(id: str, db_session: Session) -> ShowGroup:
        """Business logic for getting a group by id"""
        group = GroupRepository.get_group_by_id(id=id, db_session=db_session)
        return ShowGroup.model_validate(group)

    @staticmethod
    def get_by_link_url(link_url: str, db_session: Session) -> ShowGroup:
        """Business logic for getting a group by link url"""
        group = GroupRepository.get_group_by_link_url(link_url=link_url, db_session=db_session)
        return ShowGroup.model_validate(group)
