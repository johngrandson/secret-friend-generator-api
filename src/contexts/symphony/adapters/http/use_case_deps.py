"""Generic FastAPI dependency factory for symphony use cases.

Three sub-routers (run, spec, plan) used to declare 11 nearly identical
``get_*_use_case`` functions — same UoW build, same publisher injection,
same factory call. This module collapses them into one factory used
across all three routers.

Each generated dependency:

1. Resolves the per-use-case ``Factory`` provider from the container.
2. Builds a fresh ``SQLAlchemySymphonyUnitOfWork`` from the request session.
3. Injects the singleton ``InMemoryEventPublisher`` for mutating use cases.
4. Calls the factory with these wired dependencies.

The single-line wrappers in ``run/deps.py``, ``spec/deps.py`` and
``plan/deps.py`` keep the public ``Annotated[..., Depends(...)]`` aliases
the route handlers already import.
"""

from collections.abc import Callable
from typing import Annotated, Any, TypeVar

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.infrastructure.containers import Container
from src.infrastructure.database import get_session

T = TypeVar("T")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
_core_event_publisher = Provide[Container.core.event_publisher]


def make_use_case_dep(
    provider: Any,
    *,
    with_publisher: bool,
) -> Callable[..., Any]:
    """Return a FastAPI dependency that builds a use case from ``provider``.

    ``provider`` is a ``Provide[Container.symphony.<uc>.provider]`` marker.
    ``with_publisher`` toggles event-publisher injection — mutating use
    cases (create/approve/reject) need it; read-only ones don't.
    """
    if with_publisher:

        @inject
        def dep(
            session: SessionDep,
            factory: Callable[..., T] = Depends(provider),
            publisher: InMemoryEventPublisher = Depends(_core_event_publisher),
        ) -> T:
            return factory(
                uow=SQLAlchemySymphonyUnitOfWork(session),
                event_publisher=publisher,
            )

        return dep

    @inject
    def read_only_dep(
        session: SessionDep,
        factory: Callable[..., T] = Depends(provider),
    ) -> T:
        return factory(uow=SQLAlchemySymphonyUnitOfWork(session))

    return read_only_dep
