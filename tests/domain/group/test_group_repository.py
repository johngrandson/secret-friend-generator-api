import pytest
from sqlalchemy.orm import Session

from src.domain.group.group_repository import GroupRepository
from src.domain.group.group_schemas import GroupCreate
from src.domain.shared.domain_exceptions import NotFoundError


def test_create_group_returns_group_with_id(db_session: Session):
    group = GroupRepository.create(
        GroupCreate(name="Alpha Group", description="desc"), db_session
    )
    assert group.id is not None


def test_create_group_persists_name_and_description(db_session: Session):
    group = GroupRepository.create(
        GroupCreate(name="Beta Group", description="beta desc"), db_session
    )
    assert group.name == "Beta Group"
    assert group.description == "beta desc"


def test_create_group_generates_link_url(db_session: Session):
    group = GroupRepository.create(
        GroupCreate(name="Link Group", description="desc"), db_session
    )
    assert group.link_url is not None
    assert len(group.link_url) > 0


def test_create_group_link_url_is_unique_per_group(db_session: Session):
    g1 = GroupRepository.create(GroupCreate(name="Group One", description="d"), db_session)
    g2 = GroupRepository.create(GroupCreate(name="Group Two", description="d"), db_session)
    assert g1.link_url != g2.link_url


def test_get_all_returns_a_list(db_session: Session):
    result = GroupRepository.get_all(db_session)
    assert isinstance(result, list)


def test_get_all_returns_all_created_groups(db_session: Session):
    before = len(GroupRepository.get_all(db_session))
    GroupRepository.create(GroupCreate(name="First Group", description="d"), db_session)
    GroupRepository.create(GroupCreate(name="Second Group", description="d"), db_session)
    result = GroupRepository.get_all(db_session)
    assert len(result) == before + 2


def test_get_by_id_returns_correct_group(db_session: Session):
    group = GroupRepository.create(
        GroupCreate(name="Find Me", description="desc"), db_session
    )
    fetched = GroupRepository.get_by_id(group_id=group.id, db_session=db_session)
    assert fetched.id == group.id
    assert fetched.name == "Find Me"


def test_get_by_id_nonexistent_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError):
        GroupRepository.get_by_id(group_id=99999, db_session=db_session)


def test_get_by_link_url_returns_correct_group(db_session: Session):
    group = GroupRepository.create(
        GroupCreate(name="URL Group", description="desc"), db_session
    )
    fetched = GroupRepository.get_by_link_url(
        link_url=group.link_url, db_session=db_session
    )
    assert fetched.id == group.id


def test_get_by_link_url_nonexistent_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError):
        GroupRepository.get_by_link_url(
            link_url="nonexistent-token-xyz", db_session=db_session
        )
