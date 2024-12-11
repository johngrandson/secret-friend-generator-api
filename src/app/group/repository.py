from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..common.utils.hashing import Hasher
from ..group.model import Group
from ..group.schema import GroupCreate, ShowGroup, ShowGroups


class GroupRepository:
    @staticmethod
    def create_new_group(*, group: GroupCreate, db_session: Session):
        """Persist a new group in the database"""
        try:
            new_group = Group(**group.model_dump(exclude_unset=True))
            new_group.link_url = Hasher.generate_group_token()

            db_session.add(new_group)
            db_session.commit()
            db_session.refresh(new_group)

        except IntegrityError as e:
            db_session.rollback()

            print(f"Integrity error during group creation: {str(e)}")
            raise ValueError(
                "Group creation failed. Ensure unique constraints are met."
            )

        return new_group

    @staticmethod
    def get_all_groups(*, db_session: Session):
        try:
            groups = db_session.query(Group).all()
            pydantic_groups = [ShowGroup.model_validate(group) for group in groups]
            return ShowGroups(groups=pydantic_groups)
        except IntegrityError as e:
            print(f"Integrity error during group creation: {str(e)}")
            raise ValueError(
                "Group creation failed. Ensure unique constraints are met."
            )

        return groups

    @staticmethod
    def get_group_by_id(*, id: str, db_session: Session):
        try:
            group = db_session.query(Group).filter(Group.id == id).first()
            if not group:
                raise ValueError("Group not found")

        except IntegrityError as e:
            print(f"Integrity error during group creation: {str(e)}")
            raise ValueError(
                "Group creation failed. Ensure unique constraints are met."
            )

        return group

    @staticmethod
    def get_group_by_link_url(*, link_url: str, db_session: Session):
        try:
            group = db_session.query(Group).filter(Group.link_url == link_url).first()
            if not group:
                raise ValueError("Group not found")

        except IntegrityError as e:
            print(f"Integrity error during group creation: {str(e)}")
            raise ValueError(
                "Group creation failed. Ensure unique constraints are met."
            )

        return group
