"""Interrupt (HITL) app — db_admin agent with list_records and delete_record tools."""

import json

from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt

from src.domain.agents.config.llm_factory import create_llm
from src.domain.agents.core.factory import make_agent
from src.domain.agents.core.supervisor import make_supervisor

_RECORDS: list[dict] = [
    {"id": 1, "name": "Alice", "role": "admin"},
    {"id": 2, "name": "Bob", "role": "user"},
    {"id": 3, "name": "Carol", "role": "user"},
]


@tool
async def list_records() -> str:
    """List all records in the database.

    Returns:
        JSON string of all records.
    """
    return json.dumps(_RECORDS)


@tool
async def delete_record(record_id: int) -> str:
    """Delete a record by ID after human approval.

    Args:
        record_id: The integer ID of the record to delete.

    Returns:
        Confirmation message after approval.
    """
    record = next((r for r in _RECORDS if r["id"] == record_id), None)
    if record is None:
        return f"Record {record_id} not found."
    interrupt({"action": "delete_record", "record_id": record_id, "record": record})
    _RECORDS[:] = [r for r in _RECORDS if r["id"] != record_id]
    return f"Record {record_id} ({record['name']}) has been deleted."


def create_interrupt_app() -> CompiledStateGraph:
    """Build a supervisor graph with a db_admin agent that requires HITL on deletes.

    Returns:
        Compiled supervisor graph with an ``invoke`` method.
    """
    llm = create_llm()

    db_admin = make_agent(
        name="db_admin",
        llm=llm,
        tools=[list_records, delete_record],
        system=(
            "You are a database administrator. "
            "Use list_records to show records and delete_record to remove them. "
            "Deletes require human approval."
        ),
    )

    return make_supervisor(
        agents=[db_admin],
        llm=llm,
        supervisor_name="supervisor",
        prompt="Route all database tasks to db_admin.",
    )
