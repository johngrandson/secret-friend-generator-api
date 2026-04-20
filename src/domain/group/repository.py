from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.group.model import Group
from src.domain.group.schemas import GroupCreate
from src.domain.shared.exceptions import ConflictError, NotFoundError
from src.shared.utils.hashing_utils import Hasher


class GroupRepository:
    @staticmethod
    def create(group: GroupCreate, db_session: Session) -> Group:
        new_group = Group(**group.model_dump(exclude_unset=True))
        new_group.link_url = Hasher.generate_group_token()
        try:
            db_session.add(new_group)
            db_session.flush()
            db_session.refresh(new_group)
        except IntegrityError:
            raise ConflictError("Group creation failed. Unique constraint violated.")
        return new_group

    @staticmethod
    def get_all(db_session: Session) -> list[Group]:
        stmt = select(Group)
        return list(db_session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_id(group_id: int, db_session: Session) -> Group:
        group = db_session.get(Group, group_id)
        if not group:
            raise NotFoundError("Group not found")
        return group

    @staticmethod
    def get_by_link_url(link_url: str, db_session: Session) -> Group:
        stmt = select(Group).where(Group.link_url == link_url)
        group = db_session.execute(stmt).scalars().one_or_none()
        if not group:
            raise NotFoundError("Group not found")
        return group
