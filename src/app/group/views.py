from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Depends

from ..database.session import get_db
from ..group.model import Group
from ..group.schema import GroupCreate
from .service import GroupService

router = APIRouter(
    tags=["groups"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_group(group: GroupCreate, db_session: Session = Depends(get_db)):
    """Create a new group"""
    try:
        group: Group = GroupService.create(group=group, db_session=db_session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) or "An unexpected error occurred")
    return group


@router.get("")
def get_groups(db_session: Session = Depends(get_db)):
    """Get all groups"""
    try:
        groups = GroupService.get_all(db_session=db_session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) or "An unexpected error occurred")
    return groups

@router.get("/{id}")
def get_group_by_link(id: str, db_session: Session = Depends(get_db)):
    """Get a group by link url"""
    try:
        group: Group = GroupService.get_by_id(
            id=id, db_session=db_session
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) or "An unexpected error occurred")
    return group


@router.get("/link/{link_url}")
def get_group_by_link(link_url: str, db_session: Session = Depends(get_db)):
    """Get a group by link url"""
    try:
        group: Group = GroupService.get_by_link_url(
            link_url=link_url, db_session=db_session
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) or "An unexpected error occurred")
    return group
