-- DDL for the merchant's order table (SQLite). Apply with: sqlite3 state/merchant.db < sql/001_schema.sql   (make db does this)
-- Every payment column is a provider token. The GLOB checks make a card number structurally impossible in them: a value
-- such as 4242424242424242 does not start with 'pm_', so the database refuses it.
CREATE TABLE IF NOT EXISTS orders (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_intent_id TEXT    NOT NULL UNIQUE CHECK (payment_intent_id GLOB 'pi_*'),
    amount_cents      INTEGER NOT NULL CHECK (amount_cents > 0),
    currency          TEXT    NOT NULL CHECK (length(currency) = 3),
    status            TEXT    NOT NULL CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),
    customer_id       TEXT    NOT NULL DEFAULT '' CHECK (customer_id = '' OR customer_id GLOB 'cus_*'),
    payment_method_id TEXT    NOT NULL DEFAULT '' CHECK (payment_method_id = '' OR payment_method_id GLOB 'pm_*'),
    created_at        TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS orders_customer_idx ON orders (customer_id);
CREATE INDEX IF NOT EXISTS orders_status_idx ON orders (status);
