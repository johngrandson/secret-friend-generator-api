"""Mock data for support agent tools (customers, orders, tickets)."""

CUSTOMERS: dict[str, dict] = {
    "C-1001": {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "plan": "Pro",
        "balance": 0,
    },
    "C-1002": {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "plan": "Free",
        "balance": 29.99,
    },
    "C-1003": {
        "name": "Charlie Lee",
        "email": "charlie@example.com",
        "plan": "Enterprise",
        "balance": 0,
    },
}

ORDERS: dict[str, dict] = {
    "ORD-501": {
        "customer_id": "C-1001",
        "item": "Wireless Headphones",
        "status": "delivered",
        "total": 79.99,
    },
    "ORD-502": {
        "customer_id": "C-1002",
        "item": "USB-C Hub",
        "status": "shipped",
        "total": 34.99,
    },
    "ORD-503": {
        "customer_id": "C-1001",
        "item": "Mechanical Keyboard",
        "status": "processing",
        "total": 149.99,
    },
    "ORD-504": {
        "customer_id": "C-1003",
        "item": "Monitor Stand",
        "status": "delivered",
        "total": 59.99,
    },
}

TICKETS: list[dict] = [
    {
        "id": "TK-001",
        "customer_id": "C-1002",
        "issue": "Cannot login to dashboard",
        "status": "open",
    },
    {
        "id": "TK-002",
        "customer_id": "C-1001",
        "issue": "Billing charge mismatch",
        "status": "open",
    },
]
