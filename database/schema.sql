-- ============================================================
-- Customer Support Agent — Database Schema
-- Synthetic e-commerce data for a learning project.
-- This is NOT real company data.
-- ============================================================

CREATE TABLE customers (
    customer_id     SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    phone           VARCHAR(20),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
    product_id      SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    category        VARCHAR(100),
    price           NUMERIC(10, 2) NOT NULL,
    in_stock        BOOLEAN DEFAULT TRUE
);

CREATE TABLE orders (
    order_id        SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date      TIMESTAMP DEFAULT NOW(),
    status          VARCHAR(30) NOT NULL DEFAULT 'processing',
    -- allowed statuses (enforced in application code, kept simple here):
    -- processing, shipped, delivered, cancelled
    total_amount    NUMERIC(10, 2) NOT NULL,
    delivery_date   TIMESTAMP
);

CREATE TABLE order_items (
    order_item_id   SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL DEFAULT 1,
    unit_price      NUMERIC(10, 2) NOT NULL
);

CREATE TABLE payments (
    payment_id      SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    amount          NUMERIC(10, 2) NOT NULL,
    payment_method  VARCHAR(30),
    payment_date    TIMESTAMP DEFAULT NOW(),
    status          VARCHAR(30) DEFAULT 'completed'
);

CREATE TABLE refunds (
    refund_id       SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    reason          TEXT,
    amount          NUMERIC(10, 2) NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'requested',
    -- allowed statuses: requested, approved, rejected, completed
    requested_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE support_tickets (
    ticket_id       SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    order_id        INTEGER REFERENCES orders(order_id),  -- nullable: not every ticket is order-related
    issue           TEXT NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'open',
    -- allowed statuses: open, in_progress, resolved, closed
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Indexes on foreign keys we'll query by frequently
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_refunds_order_id ON refunds(order_id);
CREATE INDEX idx_tickets_customer_id ON support_tickets(customer_id);