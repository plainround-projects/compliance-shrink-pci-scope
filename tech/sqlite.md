# SQLite and Python's sqlite3 module

## What it is

SQLite is a small database that lives in **one ordinary file**. There is no server to start: the program opens the file and the engine
runs inside the program. Python includes a module, `sqlite3`, to talk to it with SQL (see `sql.md`).

## Why this repository uses it

The merchant needs somewhere to keep orders, and the claim is "the database holds tokens, never a card number". A real database with
constraints can *refuse* a card number, which is stronger than a promise. SQLite gives that without a server to run.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/infrastructure/sqlite_orders.py` | `SqliteOrders`: create, find, update, dump, columns, rows. |
| `sql/001_schema.sql`, `002_seed.sql`, `003_queries.sql` | The table, a sample row and the queries. |
| `state/merchant.db` | The database file (generated, git-ignored). |
| `Makefile` `queries` | `sqlite3 $(DATABASE_PATH) < sql/003_queries.sql`. |

## How it works underneath

The database is one file divided into pages. A **transaction** groups statements so they all happen or none do: `sqlite3` starts one
before an INSERT, UPDATE or DELETE, and `commit()` ends it. `executescript` runs a whole SQL script. `iterdump()` writes the whole
database as SQL text (`CREATE` and `INSERT` statements), which a text scanner can search.

## Walkthrough of this repository's use

`src/pci_scope/infrastructure/sqlite_orders.py`:

```python
    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()
```

`@contextmanager` makes `_connect()` usable after `with`. `with connection:` commits when the block ends well and rolls back on an error;
`finally: connection.close()` always closes the file.

`src/pci_scope/infrastructure/sqlite_orders.py`:

```python
    def initialize(self, schema: str) -> None:
        """Create the table from the schema script."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self._path)) as connection:
            connection.executescript(schema)
```

`closing(...)` closes the connection after the block; `executescript(schema)` creates the table. `CREATE TABLE IF NOT EXISTS` makes it safe to run again.

`src/pci_scope/infrastructure/sqlite_orders.py`:

```python
    def create(self, intent_id: str, amount_cents: int, currency: str, customer_id: str) -> Order:
        """Insert a pending order."""
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO orders (payment_intent_id, amount_cents, currency, status, customer_id, created_at) "
                "VALUES (?, ?, ?, 'pending', ?, ?)",
                (intent_id, amount_cents, currency, customer_id, self._now.now().strftime("%Y-%m-%dT%H:%M:%SZ")),
```

The `?` placeholders keep values apart from the SQL text (no SQL injection). `cursor.lastrowid` is the id SQLite gave the new row.

`src/pci_scope/infrastructure/sqlite_orders.py`:

```python
    def update(self, intent_id: str, status: str, payment_method_id: str) -> None:
        """Set the status and the saved payment-method token."""
        if status not in PAYMENT_STATUSES:
            raise ValueError(f"unknown status {status!r}")
        with self._connect() as connection:
            connection.execute(
                "UPDATE orders SET status = ?, payment_method_id = ? WHERE payment_intent_id = ?",
                (status, payment_method_id, intent_id),
```

The code refuses an unknown status **before** it reaches the database; the table's `CHECK` constraint would refuse it again.

`src/pci_scope/infrastructure/sqlite_orders.py`:

```python
    def dump(self) -> str:
        """The whole database as SQL text, for the scan and the backup."""
        with closing(sqlite3.connect(self._path)) as connection:
            return "\n".join(connection.iterdump())
```

`"\n".join(connection.iterdump())` is the whole database as text. The card scanner reads this text, because a binary SQLite file is
hard to search reliably.

`src/pci_scope/infrastructure/sqlite_orders.py`:

```python
    def columns(self) -> list[tuple[str, str]]:
        """(name, type) of every column in the orders table."""
        with closing(sqlite3.connect(self._path)) as connection:
            return [(row[1], row[2]) for row in connection.execute("PRAGMA table_info(orders)")]
```

`PRAGMA table_info(orders)` lists the columns (name, type); the evidence file `token-storage.txt` prints them to show there is no column
for a card number.

## Try it yourself

```bash
make db && sqlite3 state/merchant.db ".schema orders" | head -12
```
Creates the database and prints the table definition (`sqlite3` ships with macOS).

```bash
sqlite3 state/merchant.db "INSERT INTO orders (payment_intent_id, amount_cents, currency, status, created_at) VALUES ('4242424242424242', 1900, 'eur', 'pending', 'now');" 2>&1 | tail -1
```
Prints `CHECK constraint failed: payment_intent_id GLOB 'pi_*'`: the database refuses a card number in a token column.

```bash
make queries
```
Runs `sql/003_queries.sql` against the sample database.

```bash
.venv/bin/python -c "import sqlite3; c = sqlite3.connect(':memory:'); c.execute('CREATE TABLE t (x)'); c.execute('INSERT INTO t VALUES (1)'); print(list(c.iterdump())[:3])"
```
Prints `['BEGIN TRANSACTION;', 'CREATE TABLE t (x);', 'INSERT INTO "t" VALUES(1);']`.

## Mistakes people make

- **Putting values into SQL text by hand.** Use `?` placeholders.
- **Relying on application code alone** to keep card numbers out. The `CHECK` constraints enforce it in the data.
- **Forgetting to close connections.** The context manager closes them.
- **Scanning the binary file** instead of a dump. Text is searchable; the file is not.

## Check yourself

1. Where is a SQLite database stored?
   **Answer:** In one ordinary file; there is no server.
2. What does `iterdump()` return?
   **Answer:** The database as SQL statements, line by line.
3. Why does the code check the status before the SQL?
   **Answer:** A clear error early, and the table's constraint as a second guard.
4. What does `with connection:` do?
   **Answer:** Commits on success, rolls back on error.
5. What does the `GLOB 'pi_*'` check make impossible?
   **Answer:** Storing a card number in the payment-intent column.

## Further reading

- `sqlite3` (Python 3.12): <https://docs.python.org/3.12/library/sqlite3.html>
- SQLite documentation: <https://www.sqlite.org/docs.html>
