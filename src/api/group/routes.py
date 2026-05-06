from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_group_service
from src.api.group.schemas import GroupCreate, GroupList, GroupRead, GroupUpdate
from src.domain.group.service import GroupService

router = APIRouter()


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(
    group: GroupCreate,
    service: GroupService = Depends(get_group_service),
) -> GroupRead:
    entity = service.create(
        name=group.name,
        description=group.description,
        category=group.category,
    )
    return GroupRead.model_validate(entity)


@router.get("", response_model=GroupList)
def list_groups(
    service: GroupService = Depends(get_group_service),
) -> GroupList:
    groups = service.get_all()
    return GroupList(groups=[GroupRead.model_validate(g) for g in groups])


@router.get("/{group_id}", response_model=GroupRead)
def get_group(
    group_id: int,
    service: GroupService = Depends(get_group_service),
) -> GroupRead:
    return GroupRead.model_validate(service.get_by_id(group_id))


@router.get("/link/{link_url}", response_model=GroupRead)
def get_group_by_link(
    link_url: str,
    service: GroupService = Depends(get_group_service),
) -> GroupRead:
    return GroupRead.model_validate(service.get_by_link_url(link_url))


@router.patch("/{group_id}", response_model=GroupRead)
def update_group(
    group_id: int,
    payload: GroupUpdate,
    service: GroupService = Depends(get_group_service),
) -> GroupRead:
    entity = service.update(
        group_id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
    )
    return GroupRead.model_validate(entity)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    service: GroupService = Depends(get_group_service),
) -> None:
    service.delete(group_id)
