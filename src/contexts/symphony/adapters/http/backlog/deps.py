"""FastAPI dependency for the configured backlog adapter."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from src.contexts.symphony.domain.backlog.adapter import IBacklogAdapter
from src.infrastructure.containers import Container


@inject
def get_backlog_adapter(
    backlog: IBacklogAdapter = Depends(
        Provide[Container.symphony.linear_backlog_adapter]
    ),
) -> IBacklogAdapter:
    return backlog


BacklogAdapterDep = Annotated[IBacklogAdapter, Depends(get_backlog_adapter)]
