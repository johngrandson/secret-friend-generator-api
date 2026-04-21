from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.group.model import Group
from src.domain.group.schemas import GroupCreate, GroupUpdate
from src.shared.exceptions import ConflictError, NotFoundError
from src.shared.hashing import generate_group_token


class GroupRepository:
    @staticmethod
    def create(group: GroupCreate, db_session: Session) -> Group:
        new_group = Group(**group.model_dump(exclude_unset=True))
        new_group.link_url = generate_group_token()
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
    def update(group_id: int, payload: GroupUpdate, db_session: Session) -> Group:
        group = db_session.get(Group, group_id)
        if not group:
            raise NotFoundError("Group not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(group, key, value)
        try:
            db_session.flush()
            db_session.refresh(group)
        except IntegrityError:
            raise ConflictError("Group update failed. Unique constraint violated.")
        return group

    @staticmethod
    def delete(group_id: int, db_session: Session) -> None:
        group = db_session.get(Group, group_id)
        if not group:
            raise NotFoundError("Group not found")
        db_session.delete(group)
        db_session.flush()

    @staticmethod
    def get_by_link_url(link_url: str, db_session: Session) -> Group:
        stmt = select(Group).where(Group.link_url == link_url)
        group = db_session.execute(stmt).scalars().one_or_none()
        if not group:
            raise NotFoundError("Group not found")
        return group
