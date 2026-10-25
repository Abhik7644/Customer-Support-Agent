from backend.app.database import run_query


def test_connection_and_customers():
    rows = run_query("SELECT * FROM customers ORDER BY customer_id;")
    assert len(rows) == 3
    assert rows[0]["name"] == "Ravi Sharma"


def test_orders_join_products():
    rows = run_query(
        """
        SELECT o.order_id, o.status, p.name AS product_name
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.customer_id = %s
        ORDER BY o.order_id;
        """,
        (1,),
    )
    assert len(rows) == 2
    assert rows[0]["product_name"] == "Wireless Bluetooth Headphones"


if __name__ == "__main__":
    print(run_query("SELECT * FROM customers;"))