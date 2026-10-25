from backend.app.tools.order_tools import (
    get_my_orders,
    get_order_status,
    check_refund_status,
    check_refund_eligibility,
    create_support_ticket,
)

# Using customer_id=1 (Ravi Sharma) and customer_id=3 (Karan Mehta)
# from the seed data in Phase 6.


def test_get_my_orders():
    orders = get_my_orders.invoke({"current_customer_id": 1})
    assert len(orders) == 2  # Ravi has 2 orders in seed data


def test_get_order_status_owned():
    result = get_order_status.invoke({"order_id": 1, "current_customer_id": 1})
    assert result["status"] == "delivered"


def test_get_order_status_not_owned():
    # Order 1 belongs to customer 1, not customer 2 - should NOT be visible
    result = get_order_status.invoke({"order_id": 1, "current_customer_id": 2})
    assert "error" in result


def test_check_refund_status_exists():
    # Order 4 has a refund in seed data
    result = check_refund_status.invoke({"order_id": 4, "current_customer_id": 3})
    assert result["status"] == "requested"


def test_check_refund_eligibility_already_has_refund():
    # Order 4 already has a refund requested
    result = check_refund_eligibility.invoke({"order_id": 4, "current_customer_id": 3})
    assert result["eligible"] is False


def test_check_refund_eligibility_not_delivered():
    # Order 3 is still 'processing', not delivered
    result = check_refund_eligibility.invoke({"order_id": 3, "current_customer_id": 2})
    assert result["eligible"] is False


def test_create_support_ticket():
    result = create_support_ticket.invoke({
        "current_customer_id": 1,
        "issue": "Test ticket from Phase 7",
        "order_id": 1,
    })
    assert result["status"] == "open"
    assert "ticket_id" in result


if __name__ == "__main__":
    print("My orders (customer 1):", get_my_orders.invoke({"current_customer_id": 1}))
    print("\nOrder 1 status (as customer 1):", get_order_status.invoke({"order_id": 1, "current_customer_id": 1}))
    print("\nOrder 1 status (as customer 2 - should fail):", get_order_status.invoke({"order_id": 1, "current_customer_id": 2}))
    print("\nRefund eligibility for order 1 (customer 1):", check_refund_eligibility.invoke({"order_id": 1, "current_customer_id": 1}))