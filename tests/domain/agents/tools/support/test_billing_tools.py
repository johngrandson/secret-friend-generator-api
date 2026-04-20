"""Tests for support billing tools."""

from unittest.mock import patch

import pytest

import src.domain.agents.tools.support.billing_tools as mod


@pytest.mark.asyncio
async def test_lookup_customer_found() -> None:
    result = await mod.lookup_customer.ainvoke({"customer_id": "C-1001"})
    assert "Alice Johnson" in result
    assert "C-1001" in result


@pytest.mark.asyncio
async def test_lookup_customer_not_found() -> None:
    result = await mod.lookup_customer.ainvoke({"customer_id": "C-9999"})
    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_check_balance_zero() -> None:
    result = await mod.check_balance.ainvoke({"customer_id": "C-1001"})
    assert "no outstanding balance" in result


@pytest.mark.asyncio
async def test_check_balance_nonzero() -> None:
    result = await mod.check_balance.ainvoke({"customer_id": "C-1002"})
    assert "29.99" in result


@pytest.mark.asyncio
async def test_check_balance_not_found() -> None:
    result = await mod.check_balance.ainvoke({"customer_id": "C-9999"})
    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_issue_refund_order_not_found() -> None:
    result = await mod.issue_refund.ainvoke(
        {"order_id": "ORD-999", "reason": "defective"}
    )
    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_issue_refund_calls_interrupt() -> None:
    with patch(
        "src.domain.agents.tools.support.billing_tools.interrupt",
        return_value="yes",
    ) as mock_int:
        result = await mod.issue_refund.ainvoke(
            {"order_id": "ORD-501", "reason": "defective"}
        )
        mock_int.assert_called_once()
        call_args = mock_int.call_args[0][0]
        assert call_args["action"] == "issue_refund"
        assert call_args["order_id"] == "ORD-501"
        assert call_args["amount"] == 79.99
        assert call_args["reason"] == "defective"
    assert "79.99" in result
