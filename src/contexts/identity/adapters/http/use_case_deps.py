"""Generic FastAPI dependency factory for identity use cases.

Mirrors the symphony equivalent: collapses repeated ``get_*_use_case``
declarations into a single factory. Each generated dependency:

1. Resolves the per-use-case ``Factory`` provider from the container.
2. Builds a fresh ``SQLAlchemyIdentityUnitOfWork`` from the request session.
3. Injects the singleton ``InMemoryEventPublisher`` for mutating use cases.
4. Calls the factory with these wired dependencies.
"""

from collections.abc import Callable
from typing import TypeVar

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from src.contexts.identity.adapters.persistence.unit_of_work import (
    SQLAlchemyIdentityUnitOfWork,
)
from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.infrastructure.containers import Container
from src.infrastructure.database import SessionDep

T = TypeVar("T")

_core_event_publisher = Provide[Container.core.event_publisher]


def make_use_case_dep(
    provider: Callable[..., T],
    *,
    with_publisher: bool,
) -> Callable[..., T]:
    """Return a FastAPI dependency that builds a use case from ``provider``.

    ``provider`` is a ``Provide[Container.identity.<uc>.provider]`` marker;
    at runtime dependency-injector resolves it to a factory callable, so
    typing it as ``Callable[..., T]`` matches the resolved shape.
    ``with_publisher`` toggles event-publisher injection — mutating use
    cases (create/update/delete) need it; read-only ones don't.
    """
    if with_publisher:

        @inject
        def dep(
            session: SessionDep,
            factory: Callable[..., T] = Depends(provider),
            publisher: InMemoryEventPublisher = Depends(_core_event_publisher),
        ) -> T:
            return factory(
                uow=SQLAlchemyIdentityUnitOfWork(session),
                event_publisher=publisher,
            )

        return dep

    @inject
    def read_only_dep(
        session: SessionDep,
        factory: Callable[..., T] = Depends(provider),
    ) -> T:
        return factory(uow=SQLAlchemyIdentityUnitOfWork(session))

    return read_only_dep
