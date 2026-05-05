from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.persistence import Base, get_db
from src.infrastructure.persistence.models import (  # noqa: F401  (registers metadata)
    GroupORM,
    ParticipantORM,
    SecretFriendORM,
)
from src.infrastructure.repositories.group_repository import (
    PostgresGroupRepository,
)
from src.infrastructure.repositories.participant_repository import (
    PostgresParticipantRepository,
)
from src.domain.group.entities import Group
from src.domain.participant.entities import Participant

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    _engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)


@pytest.fixture(scope="function")
def db_session(engine) -> Session:
    """Each test runs in a transaction that is rolled back on teardown."""
    connection = engine.connect()
    txn = connection.begin()
    session = Session(connection)
    yield session
    session.close()
    txn.rollback()
    connection.close()


@pytest.fixture
def client(engine):
    """FastAPI test client with a dedicated SQLite session per request."""
    from src.app_main import api

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    api.dependency_overrides[get_db] = override_get_db
    with (
        patch("src.app_main.init_agents_registry", new_callable=AsyncMock),
        patch("src.app_main.shutdown_agents", new_callable=AsyncMock),
        TestClient(api, base_url="http://testserver/api/v1") as c,
    ):
        yield c
    api.dependency_overrides.clear()


@pytest.fixture
def group_fixture(db_session: Session):
    def _create(**overrides) -> Group:
        defaults = {"name": "Test Group", "description": "A test group"}
        merged = {**defaults, **overrides}
        repo = PostgresGroupRepository(db_session)
        return repo.create(Group(**merged))

    return _create


@pytest.fixture
def participant_fixture(db_session: Session, group_fixture):
    def _create(group=None, **overrides) -> Participant:
        group = group or group_fixture()
        defaults = {"name": "Test Participant", "group_id": group.id}
        merged = {**defaults, **overrides}
        repo = PostgresParticipantRepository(db_session)
        return repo.create(Participant(**merged))

    return _create
