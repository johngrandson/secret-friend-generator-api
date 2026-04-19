"""POST /{app_name}/invoke endpoint."""

from typing import Any

from fastapi import APIRouter

from src.api.agents.agents_dependencies import get_app
from src.api.agents.agents_message_utils import last_message_content, serialise_message
from src.api.agents.agents_schemas import InvokeBody, InvokeResponse

router = APIRouter()

# Re-export under the original private name so existing tests can import it.
_last_message_content = last_message_content


@router.post("/{app_name}/invoke", response_model=InvokeResponse)
async def invoke(app_name: str, body: InvokeBody) -> InvokeResponse:
    """Invoke *app_name* with the provided messages and return the full state."""
    app = get_app(app_name)
    messages = [m.model_dump() for m in body.messages]
    result = await app.ainvoke(
        {"messages": messages},
        config={"configurable": {"thread_id": body.thread_id}},
    )
    result_messages: list[Any] = result.get("messages", [])
    return InvokeResponse(
        messages=[serialise_message(m) for m in result_messages],
        structured_response=result.get("structured_response"),
        last_message=last_message_content(result_messages),
    )
