from langchain_core.tools import tool
from backend.app.database import run_query, run_write


@tool
def get_my_orders(current_customer_id: int) -> list[dict]:
    """
    Get all orders belonging to the currently authenticated customer.

    Use this when the customer asks something like "where are my
    orders", "show my order history", or "what have I bought".
    Does NOT take an order_id — it returns ALL of the customer's own
    orders. Never call this with any customer_id other than the
    authenticated user's own ID.

    Args:
        current_customer_id: The authenticated customer's ID (injected
            by the system, never supplied by the user's message).

    Returns:
        A list of the customer's orders with id, status, amount, and dates.
    """
    return run_query(
        """
        SELECT order_id, status, total_amount, order_date, delivery_date
        FROM orders
        WHERE customer_id = %s
        ORDER BY order_date DESC;
        """,
        (current_customer_id,),
    )


@tool
def create_refund_request(order_id: int, current_customer_id: int, reason: str) -> dict:
    """
    Create a refund request for an order.

    IMPORTANT: only call this AFTER confirming with
    check_refund_eligibility that the order is actually eligible.
    Do not call this speculatively "just in case" — creating an
    unnecessary refund request is a real action with consequences,
    not a harmless lookup.

    Args:
        order_id: The order to refund.
        current_customer_id: The authenticated customer's ID.
        reason: Why the customer is requesting a refund.

    Returns:
        The newly created refund request's ID, amount, and status.
    """
    # Re-check eligibility here too, not just trust that the agent
    # called check_refund_eligibility first. The agent SHOULD do that,
    # but we don't rely on LLM behavior alone for a real business rule -
    # this tool enforces it independently as a backend safeguard.
    eligibility = check_refund_eligibility.invoke({
        "order_id": order_id,
        "current_customer_id": current_customer_id,
    })
    if not eligibility.get("eligible"):
        return {"error": f"Cannot create refund: {eligibility.get('reason')}"}

    order_rows = run_query(
        "SELECT total_amount FROM orders WHERE order_id = %s AND customer_id = %s;",
        (order_id, current_customer_id),
    )
    if not order_rows:
        return {"error": "Order not found."}

    amount = order_rows[0]["total_amount"]

    refund_id = run_write(
        """
        INSERT INTO refunds (order_id, reason, amount, status)
        VALUES (%s, %s, %s, 'requested')
        RETURNING refund_id;
        """,
        (order_id, reason, amount),
    )

    return {
        "refund_id": refund_id,
        "amount": float(amount),
        "status": "requested",
    }



@tool
def get_order_status(order_id: int, current_customer_id: int) -> dict:
    """
    Get the status of a single specific order by its order ID.

    Use this when the customer asks about one specific order, e.g.
    "where is order #4" or "what's the status of my order 4".

    Only returns the order if it belongs to the authenticated customer
    - this prevents one customer from looking up another customer's
    order by guessing an order_id.

    Args:
        order_id: The specific order's ID.
        current_customer_id: The authenticated customer's ID (injected
            by the system, never supplied by the user's message).

    Returns:
        The order's details, or an error if not found or not owned by
        this customer.
    """
    rows = run_query(
        """
        SELECT order_id, status, total_amount, order_date, delivery_date
        FROM orders
        WHERE order_id = %s AND customer_id = %s;
        """,
        (order_id, current_customer_id),
    )
    if not rows:
        return {"error": f"No order {order_id} found for this customer."}
    return rows[0]


@tool
def check_refund_status(order_id: int, current_customer_id: int) -> dict:
    """
    Check the status of a refund request tied to a specific order.

    Use this when the customer asks "what's the status of my refund"
    or "has my refund been processed" for a known order.

    Args:
        order_id: The order the refund is tied to.
        current_customer_id: The authenticated customer's ID.

    Returns:
        The refund's status and amount, or a message if no refund
        exists for that order.
    """
    rows = run_query(
        """
        SELECT r.refund_id, r.reason, r.amount, r.status, r.requested_at
        FROM refunds r
        JOIN orders o ON o.order_id = r.order_id
        WHERE r.order_id = %s AND o.customer_id = %s;
        """,
        (order_id, current_customer_id),
    )
    if not rows:
        return {"error": f"No refund found for order {order_id}."}
    return rows[0]


@tool
def check_refund_eligibility(order_id: int, current_customer_id: int) -> dict:
    """
    Check whether an order is eligible for a refund, based on order
    status and delivery date.

    Use this BEFORE creating a refund request, to determine if the
    order qualifies. Business rule (simplified for this project):
    an order is refund-eligible if it was delivered within the last
    30 days and does not already have a refund request.

    Args:
        order_id: The order to check.
        current_customer_id: The authenticated customer's ID.

    Returns:
        A dict with 'eligible' (bool) and 'reason' (str explaining why).
    """
    rows = run_query(
        """
        SELECT o.status, o.delivery_date,
               (SELECT COUNT(*) FROM refunds r WHERE r.order_id = o.order_id) AS refund_count
        FROM orders o
        WHERE o.order_id = %s AND o.customer_id = %s;
        """,
        (order_id, current_customer_id),
    )
    if not rows:
        return {"eligible": False, "reason": "Order not found for this customer."}

    order = rows[0]

    if order["status"] != "delivered":
        return {
            "eligible": False,
            "reason": f"Order status is '{order['status']}', not 'delivered'. Only delivered orders are refund-eligible.",
        }

    if order["refund_count"] > 0:
        return {
            "eligible": False,
            "reason": "A refund request already exists for this order.",
        }

    if order["delivery_date"] is None:
        return {"eligible": False, "reason": "No delivery date on record."}

    from datetime import datetime, timezone
    days_since_delivery = (datetime.now(timezone.utc) - order["delivery_date"].replace(tzinfo=timezone.utc)).days

    if days_since_delivery > 30:
        return {
            "eligible": False,
            "reason": f"Delivered {days_since_delivery} days ago — refund window is 30 days.",
        }

    return {"eligible": True, "reason": "Order was delivered within the last 30 days and has no existing refund."}


@tool
def create_support_ticket(current_customer_id: int, issue: str, order_id: int | None = None) -> dict:
    """
    Create a new support ticket for the customer.

    Use this when the customer describes a problem that needs human
    follow-up and isn't fully resolved by information alone — e.g.
    "my product arrived damaged", "create a ticket for my issue".

    Args:
        current_customer_id: The authenticated customer's ID.
        issue: A clear description of the customer's problem.
        order_id: The related order ID, if the issue is order-specific.
            Omit if the issue isn't tied to a specific order.

    Returns:
        The newly created ticket's ID and status.
    """
    ticket_id = run_write(
        """
        INSERT INTO support_tickets (customer_id, order_id, issue, status)
        VALUES (%s, %s, %s, 'open')
        RETURNING ticket_id;
        """,
        (current_customer_id, order_id, issue),
    )
    return {"ticket_id": ticket_id, "status": "open", "issue": issue}