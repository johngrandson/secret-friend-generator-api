"""DELETE /users/{user_id} — remove a user."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.identity.adapters.http.user.router import router
from src.contexts.identity.adapters.http.user.deps import DeleteUserUseCaseDep
from src.contexts.identity.use_cases.user.delete import DeleteUserRequest


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, delete_uc: DeleteUserUseCaseDep) -> None:
    resp = await delete_uc.execute(DeleteUserRequest(user_id=user_id))
    if not resp.success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
