from langchain_core.tools import tool
from backend.app.database import run_query


@tool
def get_product_details(product_id: int) -> dict:
    """
    Look up details for a single product by its product ID.

    Use this when the customer asks about a specific product's price,
    availability, category, or description. Requires a numeric
    product_id — if the customer only gives a product name, ask them
    for the product ID, or note that name-based lookup isn't supported
    yet.

    Args:
        product_id: The numeric ID of the product to look up.

    Returns:
        A dictionary with product details, or an error message if the
        product_id doesn't exist.
    """
    rows = run_query(
        """
        SELECT product_id, name, description, category, price, in_stock
        FROM products
        WHERE product_id = %s;
        """,
        (product_id,),
    )

    if not rows:
        return {"error": f"No product found with product_id {product_id}."}

    product = rows[0]
    product["price"] = float(product["price"])  # NUMERIC comes back as Decimal
    return product