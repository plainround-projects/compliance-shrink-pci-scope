# SQL

## What it is

SQL (Structured Query Language) is the language for asking a relational database to create tables, store rows and find them. A **table**
is a grid: each **row** is one record, each **column** has a name and a type. Statements end with a semicolon; `--` starts a comment.
A **constraint** (`NOT NULL`, `UNIQUE`, `CHECK`) makes the database refuse bad data.

## Why this repository uses it

The table is the first proof: **every payment column is a provider token, and the database refuses anything else**. A card number such
as `4242424242424242` does not start with `pi_` or `pm_`, so the insert fails.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `sql/001_schema.sql` | The `orders` table, with `CHECK` constraints, and two indexes. |
| `sql/002_seed.sql` | A sample order for the queries. |
| `sql/003_queries.sql` | Queries for the evidence and the lesson. |
| `src/pci_scope/infrastructure/sqlite_orders.py` | The statements the app runs. |

## How it works underneath

The engine parses a statement, plans it, runs it and returns rows or a count. Constraints are checked on every change. An **index** is a
sorted lookup structure that lets the engine find rows without reading the whole table. `GLOB` is SQLite's case-sensitive pattern
match: `*` stands for any characters.

## Walkthrough of this repository's use

`sql/001_schema.sql`:

```sql
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
```

- `id INTEGER PRIMARY KEY AUTOINCREMENT`: a unique row number the database assigns.
- `payment_intent_id TEXT NOT NULL UNIQUE CHECK (payment_intent_id GLOB 'pi_*')`: required, never twice, and it **must start with
  `pi_`**.
- `amount_cents INTEGER ... CHECK (amount_cents > 0)`: money as whole cents, positive.
- `currency ... CHECK (length(currency) = 3)`: a three-letter code.
- `status ... CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded'))`: only known statuses.
- `customer_id ... CHECK (customer_id = '' OR customer_id GLOB 'cus_*')`: empty, or a customer token.
- `payment_method_id ... CHECK (payment_method_id = '' OR payment_method_id GLOB 'pm_*')`: empty, or a payment-method token.
- `created_at TEXT NOT NULL`: a time as text.

`sql/001_schema.sql`:

```sql
CREATE INDEX IF NOT EXISTS orders_customer_idx ON orders (customer_id);
CREATE INDEX IF NOT EXISTS orders_status_idx ON orders (status);
```

Indexes on the columns used to look orders up.

`src/pci_scope/infrastructure/sqlite_orders.py`:

```python
                "INSERT INTO orders (payment_intent_id, amount_cents, currency, status, customer_id, created_at) "
                "VALUES (?, ?, ?, 'pending', ?, ?)",
                (intent_id, amount_cents, currency, customer_id, self._now.now().strftime("%Y-%m-%dT%H:%M:%SZ")),
```

The app's insert; the `?` are placeholders, and `'pending'` is a literal inside the statement.

### The complete file `sql/001_schema.sql`, line by line

`sql/001_schema.sql` lines 1 to 15:

```sql
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
```

> **In plain words.** SQL statements end with a semicolon; `--` starts a comment. A **table** is a grid of rows and columns. A **constraint** (`NOT NULL`, `UNIQUE`, `CHECK`, `REFERENCES`) makes the database refuse bad data. An **index** speeds up lookups. A **query** (`SELECT`) reads rows.

- Creates the table `orders` if it does not exist yet. Its columns:
  - `id` of type `INTEGER`: the primary key (unique row identity).
  - `payment_intent_id` of type `TEXT`: required, never repeated, must satisfy `payment_intent_id GLOB 'pi_*'`.
  - `amount_cents` of type `INTEGER`: required, must satisfy `amount_cents > 0`.
  - `currency` of type `TEXT`: required, must satisfy `length(currency) = 3`.
  - `status` of type `TEXT`: required, must satisfy `status IN ('pending', 'succeeded', 'failed', 'refunded')`.
  - `customer_id` of type `TEXT`: required, defaults to `''`, must satisfy `customer_id = '' OR customer_id GLOB 'cus_*'`.
  - `payment_method_id` of type `TEXT`: required, defaults to `''`, must satisfy `payment_method_id = '' OR payment_method_id GLOB 'pm_*'`.
  - `created_at` of type `TEXT`: required.
- Builds an **index**, a sorted lookup structure that lets the database find rows without reading the whole table: `CREATE INDEX IF NOT EXISTS orders_customer_idx ON orders (customer_id)`.
- Builds an **index**, a sorted lookup structure that lets the database find rows without reading the whole table: `CREATE INDEX IF NOT EXISTS orders_status_idx ON orders (status)`.

### The complete file `sql/002_seed.sql`, line by line

`sql/002_seed.sql` lines 1 to 4:

```sql
-- DML: two made-up orders so the queries have something to show. The tokens are invented; no card exists behind them.
INSERT OR IGNORE INTO orders (payment_intent_id, amount_cents, currency, status, customer_id, payment_method_id, created_at) VALUES
    ('pi_0123456789abcdef01234567', 1900, 'eur', 'succeeded', 'cus_0123456789abcdef01234567', 'pm_0123456789abcdef01234567', '2026-10-26T09:00:00Z'),
    ('pi_89abcdef0123456789abcdef', 1900, 'eur', 'refunded', 'cus_0123456789abcdef01234567', 'pm_0123456789abcdef01234567', '2026-10-26T09:05:00Z');
```

> **In plain words.** SQL statements end with a semicolon; `--` starts a comment. A **table** is a grid of rows and columns. A **constraint** (`NOT NULL`, `UNIQUE`, `CHECK`, `REFERENCES`) makes the database refuse bad data. An **index** speeds up lookups. A **query** (`SELECT`) reads rows.

- `INSERT OR IGNORE INTO orders (payment_intent_id, amount_cents, currency, status, customer_id, payment_method_id, created_at) VALUES ('pi_01…`.

### The complete file `sql/003_queries.sql`, line by line

`sql/003_queries.sql` lines 1 to 1:

```sql
-- The queries behind the proof and the repeat charge, each with a line on what it shows. Run with: make queries
```

> **In plain words.** SQL statements end with a semicolon; `--` starts a comment. A **table** is a grid of rows and columns. A **constraint** (`NOT NULL`, `UNIQUE`, `CHECK`, `REFERENCES`) makes the database refuse bad data. An **index** speeds up lookups. A **query** (`SELECT`) reads rows.

- These lines are comments written by the author (`--` starts a comment); they are quoted above.

`sql/003_queries.sql` lines 3 to 4:

```sql
-- What the table can hold: every column and its type. No column is a card number, a CVV or an expiry.
SELECT name, type FROM pragma_table_info('orders');
```

- A **query**: it reads data and returns rows. `SELECT name, type FROM pragma_table_info('orders')`.

`sql/003_queries.sql` lines 6 to 9:

```sql
-- The proof, in SQL: values in any column that look like a card number (13 to 19 digits). Expect no rows.
SELECT id, payment_intent_id FROM orders
WHERE payment_intent_id GLOB '*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]*'
   OR customer_id GLOB '[0-9]*' OR payment_method_id GLOB '[0-9]*';
```

- A **query**: it reads data and returns rows. `SELECT id, payment_intent_id FROM orders WHERE payment_intent_id GLOB '*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0…`.

`sql/003_queries.sql` lines 11 to 12:

```sql
-- A repeat charge needs only these two tokens.
SELECT customer_id, payment_method_id FROM orders WHERE status = 'succeeded' AND payment_method_id <> '' LIMIT 1;
```

- A **query**: it reads data and returns rows. `SELECT customer_id, payment_method_id FROM orders WHERE status = 'succeeded' AND payment_method_id <> '' LIMIT 1`.

`sql/003_queries.sql` lines 14 to 15:

```sql
-- Revenue by status, to see refunds.
SELECT status, count(*) AS orders, sum(amount_cents) / 100.0 AS total FROM orders GROUP BY status ORDER BY status;
```

- A **query**: it reads data and returns rows. `SELECT status, count(*) AS orders, sum(amount_cents) / 100.0 AS total FROM orders GROUP BY status ORDER BY status`.

## Try it yourself

```bash
make db && sqlite3 state/merchant.db "SELECT id, payment_intent_id, status FROM orders;"
```
Creates the database and lists the seeded order.

```bash
sqlite3 state/merchant.db "INSERT INTO orders (payment_intent_id, amount_cents, currency, status, created_at) VALUES ('pm_x', 1, 'eur', 'pending', 't');" 2>&1 | tail -1
```
Prints `CHECK constraint failed: payment_intent_id GLOB 'pi_*'`.

```bash
sqlite3 state/merchant.db ".schema orders" | grep -c GLOB
```
Prints `3`: the three token checks.

```bash
grep -c "CHECK" sql/001_schema.sql
```
Counts the checks in the schema.

## Mistakes people make

- **Trusting the application alone** to keep bad data out. The table refuses it as well.
- **Storing money as a float.** Cents in an integer avoid rounding errors.
- **Using `LIKE` where case matters.** `GLOB` is case-sensitive, which is what a token check wants.
- **Pasting values into SQL text.** Use placeholders.

## Check yourself

1. What does `CHECK (payment_intent_id GLOB 'pi_*')` guarantee?
   **Answer:** Every stored value starts with `pi_`, so a card number cannot be stored there.
2. What is an index for?
   **Answer:** Finding rows without reading the whole table.
3. Why is the amount stored in cents?
   **Answer:** Whole numbers avoid rounding errors.
4. What does `UNIQUE` do?
   **Answer:** Refuses a second row with the same value.
5. What does `IF NOT EXISTS` allow?
   **Answer:** Running the script again without an error.

## Further reading

- SQLite SQL language reference: <https://www.sqlite.org/lang.html>
- `CREATE TABLE` and constraints: <https://www.sqlite.org/lang_createtable.html>; `GLOB`: <https://www.sqlite.org/lang_expr.html#glob>
