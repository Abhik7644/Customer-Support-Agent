-- ============================================================
-- Synthetic seed data — NOT real customers, orders, or transactions.
-- ============================================================

INSERT INTO customers (name, email, phone) VALUES
('Ravi Sharma', 'ravi.sharma@example.com', '9876543210'),
('Ananya Gupta', 'ananya.gupta@example.com', '9876543211'),
('Karan Mehta', 'karan.mehta@example.com', '9876543212');

INSERT INTO products (name, description, category, price, in_stock) VALUES
('Wireless Bluetooth Headphones', 'Over-ear wireless headphones with 30-hour battery life.', 'Electronics', 2499.00, TRUE),
('Stainless Steel Water Bottle', '1-litre insulated bottle, keeps drinks cold for 24 hours.', 'Home & Kitchen', 599.00, TRUE),
('Mechanical Keyboard', '87-key mechanical keyboard with blue switches.', 'Electronics', 3999.00, FALSE);

INSERT INTO orders (customer_id, status, total_amount, delivery_date) VALUES
(1, 'delivered', 2499.00, NOW() - INTERVAL '10 days'),
(1, 'shipped', 599.00, NULL),
(2, 'processing', 3999.00, NULL),
(3, 'delivered', 2499.00, NOW() - INTERVAL '3 days');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 2499.00),
(2, 2, 1, 599.00),
(3, 3, 1, 3999.00),
(4, 1, 1, 2499.00);

INSERT INTO payments (order_id, amount, payment_method) VALUES
(1, 2499.00, 'credit_card'),
(2, 599.00, 'upi'),
(3, 3999.00, 'credit_card'),
(4, 2499.00, 'upi');

INSERT INTO refunds (order_id, reason, amount, status) VALUES
(4, 'Product arrived damaged', 2499.00, 'requested');

INSERT INTO support_tickets (customer_id, order_id, issue, status) VALUES
(3, 4, 'Product arrived with a cracked casing', 'open');