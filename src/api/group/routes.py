from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.domain.group.schemas import GroupCreate, GroupList, GroupRead, GroupUpdate
from src.domain.group.service import GroupService
from src.api.dependencies import get_db

router = APIRouter()


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(group: GroupCreate, db_session: Session = Depends(get_db)):
    return GroupService.create(group=group, db_session=db_session)


@router.get("", response_model=GroupList)
def list_groups(db_session: Session = Depends(get_db)):
    return GroupService.get_all(db_session=db_session)


@router.get("/{group_id}", response_model=GroupRead)
def get_group(group_id: int, db_session: Session = Depends(get_db)):
    return GroupService.get_by_id(group_id=group_id, db_session=db_session)


@router.get("/link/{link_url}", response_model=GroupRead)
def get_group_by_link(link_url: str, db_session: Session = Depends(get_db)):
    return GroupService.get_by_link_url(link_url=link_url, db_session=db_session)


@router.patch("/{group_id}", response_model=GroupRead)
def update_group(
    group_id: int, payload: GroupUpdate, db_session: Session = Depends(get_db)
):
    return GroupService.update(
        group_id=group_id, payload=payload, db_session=db_session
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, db_session: Session = Depends(get_db)):
    GroupService.delete(group_id=group_id, db_session=db_session)
