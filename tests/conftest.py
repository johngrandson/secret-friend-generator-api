import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.domain.shared.database_base import Base
from src.domain.shared.database_session import get_db
from src.domain.group.repository import GroupRepository
from src.domain.group.schemas import GroupCreate
from src.domain.participant.repository import ParticipantRepository
from src.domain.participant.schemas import ParticipantCreate

# Import models so Base.metadata knows all tables
from src.domain.group.model import Group  # noqa: F401
from src.domain.participant.model import Participant  # noqa: F401
from src.domain.secret_friend.model import SecretFriend  # noqa: F401

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    # StaticPool ensures all connections share the same in-memory SQLite
    # database — required so that tables created here are visible to sessions
    # opened inside the FastAPI request handlers during integration tests.
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
    """FastAPI test client with a dedicated SQLite session per request.

    The routes live on the `api` sub-application (mounted at /api/v1).
    dependency_overrides must be applied on `api`, not on the outer `app`.
    We use TestClient against `api` directly and set base_url so paths like
    /api/v1/groups still work naturally in tests.
    """
    from src.app_main import api

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    api.dependency_overrides[get_db] = override_get_db
    with TestClient(api, base_url="http://testserver/api/v1") as c:
        yield c
    api.dependency_overrides.clear()


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
