import pytest
from sqlalchemy.orm import Session

from src.domain.group.service import GroupService
from src.domain.group.schemas import GroupCreate, GroupRead, GroupList, GroupUpdate
from src.shared.exceptions import NotFoundError


def test_create_returns_group_read_schema(db_session: Session):
    result = GroupService.create(
        GroupCreate(name="Service Group", description="desc"), db_session
    )
    assert isinstance(result, GroupRead)


def test_create_group_sets_correct_name(db_session: Session):
    result = GroupService.create(
        GroupCreate(name="Named Group", description="desc"), db_session
    )
    assert result.name == "Named Group"


def test_create_group_generates_link_url(db_session: Session):
    result = GroupService.create(
        GroupCreate(name="Link Group", description="desc"), db_session
    )
    assert result.link_url is not None


def test_get_all_returns_group_list_schema(db_session: Session):
    result = GroupService.get_all(db_session)
    assert isinstance(result, GroupList)


def test_get_all_includes_created_groups(db_session: Session):
    before = len(GroupService.get_all(db_session).groups)
    GroupService.create(GroupCreate(name="Group A A A", description="d"), db_session)
    GroupService.create(GroupCreate(name="Group B B B", description="d"), db_session)
    result = GroupService.get_all(db_session)
    assert len(result.groups) == before + 2


def test_get_by_id_returns_group_read_schema(db_session: Session):
    created = GroupService.create(
        GroupCreate(name="Fetch Group", description="desc"), db_session
    )
    fetched = GroupService.get_by_id(group_id=created.id, db_session=db_session)
    assert isinstance(fetched, GroupRead)
    assert fetched.id == created.id


def test_get_by_id_nonexistent_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError):
        GroupService.get_by_id(group_id=99999, db_session=db_session)


def test_get_by_link_url_returns_correct_group(db_session: Session):
    created = GroupService.create(
        GroupCreate(name="URL Service Group", description="desc"), db_session
    )
    fetched = GroupService.get_by_link_url(
        link_url=created.link_url, db_session=db_session
    )
    assert fetched.id == created.id


def test_get_by_link_url_nonexistent_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError):
        GroupService.get_by_link_url(
            link_url="does-not-exist", db_session=db_session
        )


def test_update_group_returns_updated_data(db_session: Session):
    created = GroupService.create(
        GroupCreate(name="Update Service", description="desc"), db_session
    )
    updated = GroupService.update(
        group_id=created.id, payload=GroupUpdate(name="Updated Name"), db_session=db_session
    )
    assert isinstance(updated, GroupRead)
    assert updated.name == "Updated Name"
    assert updated.id == created.id


def test_delete_group_not_found_raises(db_session: Session):
    with pytest.raises(NotFoundError):
        GroupService.delete(group_id=99999, db_session=db_session)
