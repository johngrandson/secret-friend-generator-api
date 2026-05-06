"""GetSpecUseCase — fetch a single spec by id."""

from dataclasses import dataclass
from uuid import UUID

from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.spec.dto import SpecDTO


@dataclass
class GetSpecRequest:
    spec_id: UUID


@dataclass
class GetSpecResponse:
    spec: SpecDTO | None
    success: bool
    error_message: str | None = None


class GetSpecUseCase:
    def __init__(self, uow: ISymphonyUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, request: GetSpecRequest) -> GetSpecResponse:
        async with self._uow:
            spec = await self._uow.specs.find_by_id(request.spec_id)
        if spec is None:
            return GetSpecResponse(None, False, "Spec not found.")
        return GetSpecResponse(SpecDTO.from_entity(spec), True)
