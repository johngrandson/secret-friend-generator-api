"""FastAPI dependency aliases for the Run HTTP layer.

All wiring lives in
:mod:`src.contexts.symphony.adapters.http.use_case_deps`; this module
just binds the typed ``Annotated[..., Depends(...)]`` aliases the route
handlers import.
"""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from src.contexts.symphony.adapters.http.use_case_deps import make_use_case_dep
from src.contexts.symphony.use_cases.run.cancel import CancelRunUseCase
from src.contexts.symphony.use_cases.run.create import CreateRunUseCase
from src.contexts.symphony.use_cases.run.delete import DeleteRunUseCase
from src.contexts.symphony.use_cases.run.get import GetRunUseCase
from src.contexts.symphony.use_cases.run.get_detail import GetRunDetailUseCase
from src.contexts.symphony.use_cases.run.list import ListRunsUseCase
from src.infrastructure.adapters.events.redis_run_event_bus import RedisRunEventBus
from src.infrastructure.containers import Container

get_create_run_use_case = make_use_case_dep(
    Provide[Container.symphony.create_run_use_case.provider],
    with_publisher=True,
)
get_get_run_use_case = make_use_case_dep(
    Provide[Container.symphony.get_run_use_case.provider],
    with_publisher=False,
)
get_list_runs_use_case = make_use_case_dep(
    Provide[Container.symphony.list_runs_use_case.provider],
    with_publisher=False,
)
get_run_detail_use_case = make_use_case_dep(
    Provide[Container.symphony.get_run_detail_use_case.provider],
    with_publisher=False,
)
get_cancel_run_use_case = make_use_case_dep(
    Provide[Container.symphony.cancel_run_use_case.provider],
    with_publisher=True,
)
get_delete_run_use_case = make_use_case_dep(
    Provide[Container.symphony.delete_run_use_case.provider],
    with_publisher=False,
)


CreateRunUseCaseDep = Annotated[CreateRunUseCase, Depends(get_create_run_use_case)]
GetRunUseCaseDep = Annotated[GetRunUseCase, Depends(get_get_run_use_case)]
ListRunsUseCaseDep = Annotated[ListRunsUseCase, Depends(get_list_runs_use_case)]
GetRunDetailUseCaseDep = Annotated[
    GetRunDetailUseCase, Depends(get_run_detail_use_case)
]
CancelRunUseCaseDep = Annotated[CancelRunUseCase, Depends(get_cancel_run_use_case)]
DeleteRunUseCaseDep = Annotated[DeleteRunUseCase, Depends(get_delete_run_use_case)]


@inject
def get_redis_event_bus(
    bus: RedisRunEventBus = Depends(Provide[Container.symphony.redis_event_bus]),
) -> RedisRunEventBus:
    return bus


RedisRunEventBusDep = Annotated[RedisRunEventBus, Depends(get_redis_event_bus)]
