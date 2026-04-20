"""Tests for support tech tools (orders + tickets)."""

import pytest

import src.domain.agents.tools.support.tech as mod


@pytest.mark.asyncio
async def test_lookup_order_found() -> None:
    result = await mod.lookup_order.ainvoke({"order_id": "ORD-501"})
    assert "Wireless Headphones" in result
    assert "ORD-501" in result


@pytest.mark.asyncio
async def test_lookup_order_not_found() -> None:
    result = await mod.lookup_order.ainvoke({"order_id": "ORD-999"})
    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_search_orders_found() -> None:
    result = await mod.search_orders.ainvoke({"customer_id": "C-1001"})
    assert "ORD-501" in result
    assert "ORD-503" in result


@pytest.mark.asyncio
async def test_search_orders_not_found() -> None:
    result = await mod.search_orders.ainvoke({"customer_id": "C-9999"})
    assert "no orders found" in result.lower()


@pytest.mark.asyncio
async def test_create_ticket_creates_entry() -> None:
    result = await mod.create_ticket.ainvoke(
        {"customer_id": "C-1001", "issue": "Test issue for pytest"}
    )
    assert "C-1001" in result
    assert "Test issue for pytest" in result


@pytest.mark.asyncio
async def test_list_tickets_found() -> None:
    result = await mod.list_tickets.ainvoke({"customer_id": "C-1002"})
    assert "TK-001" in result


@pytest.mark.asyncio
async def test_list_tickets_not_found() -> None:
    result = await mod.list_tickets.ainvoke({"customer_id": "C-9999"})
    assert "no tickets found" in result.lower()
