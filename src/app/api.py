from typing import List, Optional

from fastapi import APIRouter

from pydantic import BaseModel
from starlette.responses import JSONResponse

from .group.views import router as group_router
from .participant.views import router as participant_router
from .secret_friend.views import router as secret_friend_router


class ErrorMessage(BaseModel):
    msg: str


class ErrorResponse(BaseModel):
    detail: Optional[List[ErrorMessage]]


api_router = APIRouter(
    default_response_class=JSONResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)

api_router.include_router(group_router, prefix="/groups", tags=["groups"])
api_router.include_router(
    participant_router, prefix="/participants", tags=["participants"]
)
api_router.include_router(
    secret_friend_router, prefix="/secret-friends", tags=["secret-friends"]
)


@api_router.get("/healthcheck", include_in_schema=False)
def healthcheck():
    return {"status": "ok"}
