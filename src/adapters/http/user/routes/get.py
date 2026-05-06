"""GET /users/{user_id} — fetch a single user."""

from uuid import UUID

from fastapi import HTTPException, status

from src.adapters.http.user._router import router
from src.adapters.http.user.deps import GetUserUseCaseDep
from src.adapters.http.user.serializers import to_user_output
from src.use_cases.user.get import GetUserRequest


@router.get("/{user_id}")
async def get_user(user_id: UUID, get_uc: GetUserUseCaseDep) -> dict:
    resp = await get_uc.execute(GetUserRequest(user_id=user_id))
    if not resp.success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
    return to_user_output(resp.user)  # type: ignore[arg-type]
