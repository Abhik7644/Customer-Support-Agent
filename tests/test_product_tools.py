from backend.app.tools.product_tools import get_product_details


def test_existing_product():
    result = get_product_details.invoke({"product_id": 101})
    assert result["name"] == "Wireless Bluetooth Headphones"
    assert result["in_stock"] is True


def test_missing_product():
    result = get_product_details.invoke({"product_id": 999})
    assert "error" in result


if __name__ == "__main__":
    # Quick manual run without pytest, so you can see the actual output
    print("Test 1 — existing product (101):")
    print(get_product_details.invoke({"product_id": 101}))

    print("\nTest 2 — missing product (999):")
    print(get_product_details.invoke({"product_id": 999}))