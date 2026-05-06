"""Integration tests for event publication via real SQLAlchemyIdentityUnitOfWork.

These exercise the production path that AsyncMock-based unit tests cannot:
the adapter returns a fresh User from `to_entity(model)`, so events MUST be
collected from the input entity (not the repo return value) — see
`docs/event-publication-pattern.md`.

If the use-case regresses to `saved.pull_events()`, these tests fail.
"""

from src.contexts.identity.adapters.persistence.unit_of_work import (
    SQLAlchemyIdentityUnitOfWork,
)
from src.contexts.identity.domain.user.events import UserCreated, UserDeleted, UserUpdated
from src.contexts.identity.use_cases.user.create import CreateUserRequest, CreateUserUseCase
from src.contexts.identity.use_cases.user.delete import DeleteUserRequest, DeleteUserUseCase
from src.contexts.identity.use_cases.user.update import UpdateUserRequest, UpdateUserUseCase


async def test_create_user_publishes_user_created_event(async_session, fake_publisher):
    uow = SQLAlchemyIdentityUnitOfWork(async_session)
    use_case = CreateUserUseCase(uow=uow, event_publisher=fake_publisher)

    resp = await use_case.execute(
        CreateUserRequest(email="evt-create@example.com", name="Alice")
    )

    assert resp.success is True
    created = [e for e in fake_publisher.published if isinstance(e, UserCreated)]
    assert len(created) == 1
    assert created[0].email == "evt-create@example.com"
    assert created[0].name == "Alice"


async def test_update_user_publishes_user_updated_event(async_session, fake_publisher):
    uow = SQLAlchemyIdentityUnitOfWork(async_session)
    create_uc = CreateUserUseCase(uow=uow, event_publisher=fake_publisher)
    update_uc = UpdateUserUseCase(uow=uow, event_publisher=fake_publisher)

    create_resp = await create_uc.execute(
        CreateUserRequest(email="evt-update@example.com", name="Before")
    )
    fake_publisher.published.clear()  # discard the create event

    update_resp = await update_uc.execute(
        UpdateUserRequest(user_id=create_resp.user.id, name="After")
    )

    assert update_resp.success is True
    updated = [e for e in fake_publisher.published if isinstance(e, UserUpdated)]
    assert len(updated) == 1
    assert updated[0].user_id == create_resp.user.id


async def test_delete_user_publishes_user_deleted_event(async_session, fake_publisher):
    uow = SQLAlchemyIdentityUnitOfWork(async_session)
    create_uc = CreateUserUseCase(uow=uow, event_publisher=fake_publisher)
    delete_uc = DeleteUserUseCase(uow=uow, event_publisher=fake_publisher)

    create_resp = await create_uc.execute(
        CreateUserRequest(email="evt-delete@example.com", name="Doomed")
    )
    fake_publisher.published.clear()

    delete_resp = await delete_uc.execute(
        DeleteUserRequest(user_id=create_resp.user.id)
    )

    assert delete_resp.success is True
    deleted = [e for e in fake_publisher.published if isinstance(e, UserDeleted)]
    assert len(deleted) == 1
    assert deleted[0].user_id == create_resp.user.id
