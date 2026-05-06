"""GetRunUseCase — fetch a single run by id."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.dto import RunDTO


@dataclass
class GetRunRequest:
    run_id: UUID


@dataclass
class GetRunResponse:
    run: RunDTO | None
    success: bool
    error_message: str | None = None


class GetRunUseCase:
    def __init__(self, uow: ISymphonyUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, request: GetRunRequest) -> GetRunResponse:
        async with self._uow:
            run = await self._uow.runs.find_by_id(request.run_id)
        if run is None:
            return GetRunResponse(None, False, "Run not found.")
        return GetRunResponse(RunDTO.from_entity(run), True)
