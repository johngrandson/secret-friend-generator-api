from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.domain.group.group_schemas import GroupCreate, GroupList, GroupRead
from src.domain.group.group_service import GroupService
from src.domain.shared.database_session import get_db
from src.domain.shared.database_transaction import transaction
from src.domain.shared.domain_exceptions import ConflictError, NotFoundError

router = APIRouter()


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(group: GroupCreate, db_session: Session = Depends(get_db)):
    try:
        with transaction(db_session):
            return GroupService.create(group=group, db_session=db_session)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=GroupList)
def list_groups(db_session: Session = Depends(get_db)):
    return GroupService.get_all(db_session=db_session)


@router.get("/{group_id}", response_model=GroupRead)
def get_group(group_id: int, db_session: Session = Depends(get_db)):
    try:
        return GroupService.get_by_id(group_id=group_id, db_session=db_session)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/link/{link_url}", response_model=GroupRead)
def get_group_by_link(link_url: str, db_session: Session = Depends(get_db)):
    try:
        return GroupService.get_by_link_url(link_url=link_url, db_session=db_session)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
