-- DML: two made-up orders so the queries have something to show. The tokens are invented; no card exists behind them.
INSERT OR IGNORE INTO orders (payment_intent_id, amount_cents, currency, status, customer_id, payment_method_id, created_at) VALUES
    ('pi_0123456789abcdef01234567', 1900, 'eur', 'succeeded', 'cus_0123456789abcdef01234567', 'pm_0123456789abcdef01234567', '2026-10-26T09:00:00Z'),
    ('pi_89abcdef0123456789abcdef', 1900, 'eur', 'refunded', 'cus_0123456789abcdef01234567', 'pm_0123456789abcdef01234567', '2026-10-26T09:05:00Z');
