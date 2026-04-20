"""Tests for support returns tools."""

from unittest.mock import patch

import pytest

import src.domain.agents.tools.support.returns as mod


@pytest.mark.asyncio
async def test_initiate_return_not_found() -> None:
    result = await mod.initiate_return.ainvoke(
        {"order_id": "ORD-999", "reason": "wrong item"}
    )
    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_initiate_return_not_delivered() -> None:
    # ORD-502 has status "shipped", not "delivered"
    result = await mod.initiate_return.ainvoke(
        {"order_id": "ORD-502", "reason": "changed mind"}
    )
    assert "cannot be returned" in result.lower()
    assert "shipped" in result


@pytest.mark.asyncio
async def test_initiate_return_calls_interrupt() -> None:
    with patch(
        "src.domain.agents.tools.support.returns.interrupt",
        return_value="yes",
    ) as mock_int:
        result = await mod.initiate_return.ainvoke(
            {"order_id": "ORD-501", "reason": "wrong item"}
        )
        mock_int.assert_called_once()
        call_args = mock_int.call_args[0][0]
        assert call_args["action"] == "initiate_return"
        assert call_args["order_id"] == "ORD-501"
        assert call_args["item"] == "Wireless Headphones"
        assert call_args["reason"] == "wrong item"
    assert "ORD-501" in result
