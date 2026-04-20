"""Tests for support escalation tools."""

from unittest.mock import patch

import pytest

import src.domain.agents.tools.support.escalation_tools as mod


def test_escalate_to_human_tool_name() -> None:
    assert mod.escalate_to_human.name == "escalate_to_human"


def test_escalate_to_human_is_callable() -> None:
    assert callable(mod.escalate_to_human)


@pytest.mark.asyncio
async def test_escalate_to_human_calls_interrupt() -> None:
    with patch(
        "src.domain.agents.tools.support.escalation_tools.interrupt",
        return_value="yes",
    ) as mock_int:
        result = await mod.escalate_to_human.ainvoke(
            {"reason": "complex billing dispute", "customer_id": "C-1001"}
        )
        mock_int.assert_called_once()
        call_args = mock_int.call_args[0][0]
        assert call_args["action"] == "escalate_to_human"
        assert call_args["customer_id"] == "C-1001"
        assert call_args["reason"] == "complex billing dispute"
    assert "C-1001" in result
