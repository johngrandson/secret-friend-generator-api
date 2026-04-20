"""Tests for support mock data constants."""

from src.domain.agents.tools.support.mock_data import (
    CUSTOMERS,
    ORDERS,
    TICKETS,
)


def test_customers_has_expected_ids() -> None:
    assert "C-1001" in CUSTOMERS
    assert "C-1002" in CUSTOMERS
    assert "C-1003" in CUSTOMERS


def test_customer_fields_present() -> None:
    alice = CUSTOMERS["C-1001"]
    assert alice["name"] == "Alice Johnson"
    assert alice["email"] == "alice@example.com"
    assert alice["plan"] == "Pro"
    assert alice["balance"] == 0


def test_orders_has_expected_ids() -> None:
    for oid in ("ORD-501", "ORD-502", "ORD-503", "ORD-504"):
        assert oid in ORDERS


def test_order_fields_present() -> None:
    order = ORDERS["ORD-501"]
    assert order["customer_id"] == "C-1001"
    assert order["item"] == "Wireless Headphones"
    assert order["status"] == "delivered"
    assert order["total"] == 79.99


def test_tickets_has_two_entries() -> None:
    assert len(TICKETS) >= 2


def test_ticket_fields_present() -> None:
    tk = next(t for t in TICKETS if t["id"] == "TK-001")
    assert tk["customer_id"] == "C-1002"
    assert tk["status"] == "open"
