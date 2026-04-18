from fastapi import APIRouter
from starlette.responses import JSONResponse

from src.api.api_error_schemas import ErrorResponse
from src.api.group.group_routes import router as group_router
from src.api.participant.participant_routes import router as participant_router
from src.api.secret_friend.secret_friend_routes import router as secret_friend_router

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
api_router.include_router(participant_router, prefix="/participants", tags=["participants"])
api_router.include_router(
    secret_friend_router, prefix="/secret-friends", tags=["secret-friends"]
)


@api_router.get("/healthcheck", include_in_schema=False)
def healthcheck():
    return {"status": "ok"}
