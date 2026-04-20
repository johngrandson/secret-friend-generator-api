"""POST /{app_name}/resume — resume a human-in-the-loop interrupt."""

from fastapi import APIRouter
from langgraph.types import Command

from src.api.agents.dependencies import get_app
from src.api.agents.message_utils import last_message_content, serialise_message
from src.api.agents.schemas import InvokeResponse, ResumeBody

router = APIRouter()


@router.post("/{app_name}/resume", response_model=InvokeResponse)
async def resume(app_name: str, body: ResumeBody) -> InvokeResponse:
    """Resume *app_name* from an interrupt with the provided decision."""
    app = get_app(app_name)
    result = await app.ainvoke(
        Command(resume=body.decision),
        config={"configurable": {"thread_id": body.thread_id}},
    )
    result_messages = result.get("messages", []) if isinstance(result, dict) else []
    structured = result.get("structured_response") if isinstance(result, dict) else None
    return InvokeResponse(
        messages=[serialise_message(m) for m in result_messages],
        structured_response=structured,
        last_message=last_message_content(result_messages),
    )
