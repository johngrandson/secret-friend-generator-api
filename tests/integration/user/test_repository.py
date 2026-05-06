"""Integration tests for SQLAlchemyUserRepository against SQLite in-memory."""

from uuid import uuid4

from src.adapters.persistence.user.repository import SQLAlchemyUserRepository
from src.domain.user.email import Email
from src.domain.user.entity import User


def _make_user(email: str = "repo@example.com", name: str = "Repo User") -> User:
    return User.create(email=Email(email), name=name)


async def test_save_and_find_by_id(async_session):
    repo = SQLAlchemyUserRepository(async_session)
    user = _make_user()

    saved = await repo.save(user)
    found = await repo.find_by_id(saved.id)

    assert found is not None
    assert found.id == saved.id
    assert str(found.email) == "repo@example.com"


async def test_find_by_email(async_session):
    repo = SQLAlchemyUserRepository(async_session)
    user = _make_user("find@example.com")
    await repo.save(user)

    found = await repo.find_by_email(Email("find@example.com"))

    assert found is not None
    assert found.name == "Repo User"


async def test_find_by_email_returns_none_when_missing(async_session):
    repo = SQLAlchemyUserRepository(async_session)

    result = await repo.find_by_email(Email("missing@example.com"))

    assert result is None


async def test_list_returns_saved_users(async_session):
    repo = SQLAlchemyUserRepository(async_session)
    await repo.save(_make_user("list1@example.com", "User One"))
    await repo.save(_make_user("list2@example.com", "User Two"))

    users = await repo.list(limit=10, offset=0)

    emails = {str(u.email) for u in users}
    assert "list1@example.com" in emails
    assert "list2@example.com" in emails


async def test_list_pagination(async_session):
    repo = SQLAlchemyUserRepository(async_session)
    for i in range(5):
        await repo.save(_make_user(f"page{i}@example.com", f"User {i}"))

    page1 = await repo.list(limit=2, offset=0)
    page2 = await repo.list(limit=2, offset=2)

    assert len(page1) == 2
    assert len(page2) == 2
    assert {str(u.email) for u in page1}.isdisjoint({str(u.email) for u in page2})


async def test_update_user(async_session):
    repo = SQLAlchemyUserRepository(async_session)
    user = _make_user("upd@example.com", "Before")
    saved = await repo.save(user)

    saved.update_name("After")
    updated = await repo.update(saved)

    assert updated.name == "After"


async def test_delete_existing_user(async_session):
    repo = SQLAlchemyUserRepository(async_session)
    user = _make_user("del@example.com")
    saved = await repo.save(user)

    deleted = await repo.delete(saved.id)
    found = await repo.find_by_id(saved.id)

    assert deleted is True
    assert found is None


async def test_delete_nonexistent_returns_false(async_session):
    repo = SQLAlchemyUserRepository(async_session)

    result = await repo.delete(uuid4())

    assert result is False
