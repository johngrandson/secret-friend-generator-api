"""GET /users/ — list users with pagination."""

from src.adapters.http.user._router import router
from src.adapters.http.user.deps import ListUsersUseCaseDep
from src.adapters.http.user.serializers import to_user_output
from src.use_cases.user.list import ListUsersRequest


@router.get("/")
async def list_users(
    list_uc: ListUsersUseCaseDep,
    limit: int = 20,
    offset: int = 0,
) -> list:
    resp = await list_uc.execute(ListUsersRequest(limit=limit, offset=offset))
    return [to_user_output(u) for u in resp.users]
