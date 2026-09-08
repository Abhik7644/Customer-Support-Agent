"""
Temporary in-memory product data, standing in for the PostgreSQL
'products' table we'll build in Phase 6.

IMPORTANT: this file exists only so we can build and test tools before
the real database exists. When Phase 6/7 land, get_product_details()
in product_tools.py will be rewritten to query PostgreSQL instead of
this dictionary — nothing that calls the tool will need to change.
"""

MOCK_PRODUCTS = {
    101: {
        "product_id": 101,
        "name": "Wireless Bluetooth Headphones",
        "price": 2499.00,
        "category": "Electronics",
        "in_stock": True,
        "description": "Over-ear wireless headphones with 30-hour battery life.",
    },
    102: {
        "product_id": 102,
        "name": "Stainless Steel Water Bottle",
        "price": 599.00,
        "category": "Home & Kitchen",
        "in_stock": True,
        "description": "1-litre insulated bottle, keeps drinks cold for 24 hours.",
    },
    103: {
        "product_id": 103,
        "name": "Mechanical Keyboard",
        "price": 3999.00,
        "category": "Electronics",
        "in_stock": False,
        "description": "87-key mechanical keyboard with blue switches.",
    },
}