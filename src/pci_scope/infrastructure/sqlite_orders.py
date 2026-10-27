"""Orders in SQLite. The schema has no column that could hold a card number, only provider tokens."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

from pci_scope.domain.payment import PAYMENT_STATUSES, Order


class SqliteOrders:
    """The merchant's order table (sql/001_schema.sql)."""

    def __init__(self, path: Path, now: type[datetime] = datetime) -> None:
        self._path = path
        self._now = now

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self, schema: str) -> None:
        """Create the table from the schema script."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self._path)) as connection:
            connection.executescript(schema)

    def create(self, intent_id: str, amount_cents: int, currency: str, customer_id: str) -> Order:
        """Insert a pending order."""
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO orders (payment_intent_id, amount_cents, currency, status, customer_id, created_at) "
                "VALUES (?, ?, ?, 'pending', ?, ?)",
                (intent_id, amount_cents, currency, customer_id, self._now.now().strftime("%Y-%m-%dT%H:%M:%SZ")),
            )
        return Order(int(cursor.lastrowid or 0), intent_id, amount_cents, currency, "pending", customer_id)

    def find(self, intent_id: str) -> Order | None:
        """The order for a payment intent."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, payment_intent_id, amount_cents, currency, status, customer_id, payment_method_id "
                "FROM orders WHERE payment_intent_id = ?",
                (intent_id,),
            ).fetchone()
        return Order(*row) if row else None

    def update(self, intent_id: str, status: str, payment_method_id: str) -> None:
        """Set the status and the saved payment-method token."""
        if status not in PAYMENT_STATUSES:
            raise ValueError(f"unknown status {status!r}")
        with self._connect() as connection:
            connection.execute(
                "UPDATE orders SET status = ?, payment_method_id = ? WHERE payment_intent_id = ?",
                (status, payment_method_id, intent_id),
            )

    def dump(self) -> str:
        """The whole database as SQL text, for the scan and the backup."""
        with closing(sqlite3.connect(self._path)) as connection:
            return "\n".join(connection.iterdump())

    def columns(self) -> list[tuple[str, str]]:
        """(name, type) of every column in the orders table."""
        with closing(sqlite3.connect(self._path)) as connection:
            return [(row[1], row[2]) for row in connection.execute("PRAGMA table_info(orders)")]

    def rows(self, limit: int = 5) -> list[tuple[object, ...]]:
        """The first rows, for the evidence."""
        with closing(sqlite3.connect(self._path)) as connection:
            return connection.execute(
                "SELECT id, payment_intent_id, status, customer_id, payment_method_id FROM orders ORDER BY id LIMIT ?",
                (limit,),
            ).fetchall()
