"""PATCH /users/{user_id} — update name and/or active status."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.identity.adapters.http.user.router import router
from src.contexts.identity.adapters.http.user.deps import UpdateUserUseCaseDep
from src.contexts.identity.adapters.http.user.schemas import UpdateUserInput
from src.contexts.identity.adapters.http.user.serializers import to_user_output
from src.contexts.identity.use_cases.user.update import UpdateUserRequest


@router.patch("/{user_id}")
async def update_user(
    user_id: UUID,
    data: UpdateUserInput,
    update_uc: UpdateUserUseCaseDep,
) -> dict:
    resp = await update_uc.execute(
        UpdateUserRequest(user_id=user_id, name=data.name, is_active=data.is_active)
    )
    if not resp.success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
    assert resp.user is not None
    return to_user_output(resp.user)
