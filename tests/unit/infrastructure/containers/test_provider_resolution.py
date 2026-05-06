"""Unit tests verifying that each DI provider resolves to the expected concrete class.

Factories are called with minimal fakes (AsyncMock sessions, InMemoryEventPublisher)
so the tests stay pure-unit — no DB, no network. Singleton identity is also asserted
for the shared infrastructure providers in CoreContainer.

For the DB-engine/session-factory singleton tests the CoreContainer's config provider
is overridden with a Settings object that carries a valid SQLite URL — this avoids a
dependency on DATABASE_URL being set in the test environment while still exercising
the actual SQLAlchemy construction path.
"""

from collections.abc import Generator

import pytest
from dependency_injector import providers
from unittest.mock import AsyncMock

from src.contexts.identity.adapters.persistence.unit_of_work import (
    SQLAlchemyIdentityUnitOfWork,
)
from src.contexts.identity.use_cases.user.create import CreateUserUseCase
from src.contexts.identity.use_cases.user.delete import DeleteUserUseCase
from src.contexts.identity.use_cases.user.get import GetUserUseCase
from src.contexts.identity.use_cases.user.list import ListUsersUseCase
from src.contexts.identity.use_cases.user.update import UpdateUserUseCase
from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.contexts.symphony.use_cases.run.create import CreateRunUseCase
from src.contexts.symphony.use_cases.run.get import GetRunUseCase
from src.contexts.symphony.use_cases.run.list import ListRunsUseCase
from src.contexts.symphony.use_cases.spec.approve import ApproveSpecUseCase
from src.contexts.symphony.use_cases.spec.create import CreateSpecUseCase
from src.contexts.symphony.use_cases.spec.get import GetSpecUseCase
from src.contexts.symphony.use_cases.spec.list_for_run import ListSpecsForRunUseCase
from src.contexts.symphony.use_cases.spec.reject import RejectSpecUseCase
from src.contexts.symphony.use_cases.plan.approve import ApprovePlanUseCase
from src.contexts.symphony.use_cases.plan.create import CreatePlanUseCase
from src.contexts.symphony.use_cases.plan.get import GetPlanUseCase
from src.contexts.symphony.use_cases.plan.list_for_run import ListPlansForRunUseCase
from src.contexts.symphony.use_cases.plan.reject import RejectPlanUseCase
from src.infrastructure.adapters.events.in_memory_publisher import InMemoryEventPublisher
from src.infrastructure.config import Settings
from src.infrastructure.containers import Container

_TEST_SETTINGS = Settings(
    DATABASE_URL="sqlite+aiosqlite:///:memory:",
    ENV="test",
)


@pytest.fixture
def container() -> Container:
    """Fresh Container instance per test — no side effects from wiring."""
    return Container()


@pytest.fixture
def container_with_test_db() -> Generator[Container, None, None]:
    """Container with core.config overridden to use SQLite so engine providers resolve."""
    c = Container()
    c.core.config.override(providers.Object(_TEST_SETTINGS))
    yield c
    c.core.config.reset_override()
    # Reset singletons so subsequent tests start with a clean engine/factory
    engine_provider: providers.Singleton = c.core.db_engine  # type: ignore[assignment]
    session_provider: providers.Singleton = c.core.db_session_factory  # type: ignore[assignment]
    engine_provider.reset()
    session_provider.reset()


# ---------------------------------------------------------------------------
# CoreContainer singleton assertions
# ---------------------------------------------------------------------------


def test_event_publisher_is_singleton(container: Container) -> None:
    """Repeated calls to event_publisher() return the identical object."""
    assert container.core.event_publisher() is container.core.event_publisher()


def test_db_engine_is_singleton(container_with_test_db: Container) -> None:
    """Repeated calls to db_engine() return the identical engine object."""
    c = container_with_test_db
    assert c.core.db_engine() is c.core.db_engine()


def test_db_session_factory_is_singleton(container_with_test_db: Container) -> None:
    """Repeated calls to db_session_factory() return the identical factory."""
    c = container_with_test_db
    assert c.core.db_session_factory() is c.core.db_session_factory()


def test_config_is_singleton(container: Container) -> None:
    """Repeated calls to config() return the identical Settings object."""
    assert container.core.config() is container.core.config()


def test_event_publisher_resolves_to_in_memory_publisher(container: Container) -> None:
    """core.event_publisher resolves to InMemoryEventPublisher."""
    assert isinstance(container.core.event_publisher(), InMemoryEventPublisher)


# ---------------------------------------------------------------------------
# IdentityContainer — UoW factory
# ---------------------------------------------------------------------------


def test_identity_uow_factory_returns_sqlalchemy_uow(container: Container) -> None:
    """identity.identity_uow factory produces SQLAlchemyIdentityUnitOfWork."""
    session = AsyncMock()
    instance = container.identity.identity_uow(session)
    assert isinstance(instance, SQLAlchemyIdentityUnitOfWork)


# ---------------------------------------------------------------------------
# IdentityContainer — use-case providers
# ---------------------------------------------------------------------------

_IDENTITY_USE_CASES_WITH_PUBLISHER = [
    ("create_user_use_case", CreateUserUseCase),
    ("delete_user_use_case", DeleteUserUseCase),
    ("update_user_use_case", UpdateUserUseCase),
]

_IDENTITY_USE_CASES_UOW_ONLY = [
    ("get_user_use_case", GetUserUseCase),
    ("list_users_use_case", ListUsersUseCase),
]


@pytest.mark.parametrize("provider_name,expected_class", _IDENTITY_USE_CASES_WITH_PUBLISHER)
def test_identity_use_case_with_publisher_resolves(
    container: Container, provider_name: str, expected_class: type
) -> None:
    """Identity use cases that need uow + event_publisher resolve to correct class."""
    uow = SQLAlchemyIdentityUnitOfWork(AsyncMock())
    publisher = InMemoryEventPublisher()
    factory = getattr(container.identity, provider_name)
    instance = factory(uow=uow, event_publisher=publisher)
    assert isinstance(instance, expected_class)


@pytest.mark.parametrize("provider_name,expected_class", _IDENTITY_USE_CASES_UOW_ONLY)
def test_identity_use_case_uow_only_resolves(
    container: Container, provider_name: str, expected_class: type
) -> None:
    """Identity use cases that need only uow resolve to correct class."""
    uow = SQLAlchemyIdentityUnitOfWork(AsyncMock())
    factory = getattr(container.identity, provider_name)
    instance = factory(uow=uow)
    assert isinstance(instance, expected_class)


# ---------------------------------------------------------------------------
# SymphonyContainer — UoW factory
# ---------------------------------------------------------------------------


def test_symphony_uow_factory_returns_sqlalchemy_uow(container: Container) -> None:
    """symphony.symphony_uow factory produces SQLAlchemySymphonyUnitOfWork."""
    session = AsyncMock()
    instance = container.symphony.symphony_uow(session)
    assert isinstance(instance, SQLAlchemySymphonyUnitOfWork)


# ---------------------------------------------------------------------------
# SymphonyContainer — use-case providers
# ---------------------------------------------------------------------------

_SYMPHONY_USE_CASES_WITH_PUBLISHER = [
    ("create_run_use_case", CreateRunUseCase),
    ("create_spec_use_case", CreateSpecUseCase),
    ("approve_spec_use_case", ApproveSpecUseCase),
    ("reject_spec_use_case", RejectSpecUseCase),
    ("create_plan_use_case", CreatePlanUseCase),
    ("approve_plan_use_case", ApprovePlanUseCase),
    ("reject_plan_use_case", RejectPlanUseCase),
]

_SYMPHONY_USE_CASES_UOW_ONLY = [
    ("get_run_use_case", GetRunUseCase),
    ("list_runs_use_case", ListRunsUseCase),
    ("get_spec_use_case", GetSpecUseCase),
    ("list_specs_for_run_use_case", ListSpecsForRunUseCase),
    ("get_plan_use_case", GetPlanUseCase),
    ("list_plans_for_run_use_case", ListPlansForRunUseCase),
]


@pytest.mark.parametrize("provider_name,expected_class", _SYMPHONY_USE_CASES_WITH_PUBLISHER)
def test_symphony_use_case_with_publisher_resolves(
    container: Container, provider_name: str, expected_class: type
) -> None:
    """Symphony use cases that need uow + event_publisher resolve to correct class."""
    uow = SQLAlchemySymphonyUnitOfWork(AsyncMock())
    publisher = InMemoryEventPublisher()
    factory = getattr(container.symphony, provider_name)
    instance = factory(uow=uow, event_publisher=publisher)
    assert isinstance(instance, expected_class)


@pytest.mark.parametrize("provider_name,expected_class", _SYMPHONY_USE_CASES_UOW_ONLY)
def test_symphony_use_case_uow_only_resolves(
    container: Container, provider_name: str, expected_class: type
) -> None:
    """Symphony use cases that need only uow resolve to correct class."""
    uow = SQLAlchemySymphonyUnitOfWork(AsyncMock())
    factory = getattr(container.symphony, provider_name)
    instance = factory(uow=uow)
    assert isinstance(instance, expected_class)
