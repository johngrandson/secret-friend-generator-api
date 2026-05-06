"""POST /users/ — create a new user."""

from fastapi import HTTPException, status

from src.contexts.identity.adapters.http.user.router import router
from src.contexts.identity.adapters.http.user.deps import CreateUserUseCaseDep
from src.contexts.identity.adapters.http.user.schemas import CreateUserInput
from src.contexts.identity.adapters.http.user.serializers import to_user_output
from src.contexts.identity.use_cases.user.create import CreateUserRequest


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: CreateUserInput,
    create_uc: CreateUserUseCaseDep,
) -> dict:
    resp = await create_uc.execute(CreateUserRequest(email=data.email, name=data.name))
    if not resp.success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.user is not None
    return to_user_output(resp.user)
