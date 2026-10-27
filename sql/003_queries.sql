-- The queries behind the proof and the repeat charge, each with a line on what it shows. Run with: make queries

-- What the table can hold: every column and its type. No column is a card number, a CVV or an expiry.
SELECT name, type FROM pragma_table_info('orders');

-- The proof, in SQL: values in any column that look like a card number (13 to 19 digits). Expect no rows.
SELECT id, payment_intent_id FROM orders
WHERE payment_intent_id GLOB '*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]*'
   OR customer_id GLOB '[0-9]*' OR payment_method_id GLOB '[0-9]*';

-- A repeat charge needs only these two tokens.
SELECT customer_id, payment_method_id FROM orders WHERE status = 'succeeded' AND payment_method_id <> '' LIMIT 1;

-- Revenue by status, to see refunds.
SELECT status, count(*) AS orders, sum(amount_cents) / 100.0 AS total FROM orders GROUP BY status ORDER BY status;
