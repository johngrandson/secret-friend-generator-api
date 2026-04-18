import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from src.domain.shared.database_base import Base
from src.domain.shared.database_session import get_db
from src.domain.group.group_repository import GroupRepository
from src.domain.group.group_schemas import GroupCreate
from src.domain.participant.participant_repository import ParticipantRepository
from src.domain.participant.participant_schemas import ParticipantCreate

# Import models so Base.metadata knows all tables
from src.domain.group.group_model import Group  # noqa: F401
from src.domain.participant.participant_model import Participant  # noqa: F401
from src.domain.secret_friend.secret_friend_model import SecretFriend  # noqa: F401

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    _engine = create_engine(TEST_DATABASE_URL)
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
def client(db_session: Session):
    """FastAPI test client with overridden db dependency."""
    from src.app_main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def group_fixture(db_session: Session):
    def _create(**overrides):
        defaults = {"name": "Test Group", "description": "A test group"}
        return GroupRepository.create(
            GroupCreate(**{**defaults, **overrides}), db_session
        )
    return _create


@pytest.fixture
def participant_fixture(db_session: Session, group_fixture):
    def _create(group=None, **overrides):
        group = group or group_fixture()
        defaults = {"name": "Test Participant", "group_id": group.id}
        return ParticipantRepository.create(
            ParticipantCreate(**{**defaults, **overrides}), db_session
        )
    return _create
