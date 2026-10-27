# logging

## What it is

`logging` is Python's standard way to record what a program does. Code asks for a **logger** by name and calls
`logger.info(...)`; **handlers** send each **record** somewhere; a **formatter** decides what the line looks like; the level
(`DEBUG`, `INFO`, `WARNING`, `ERROR`) decides what is kept.

## Why this repository uses it

Logs are one of the places card data leaks. The naive app logs the whole form on purpose, so the scanner has something to find. The
redesigned apps log only whitelisted fields and **never a request body**, and that is part of the proof.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/infrastructure/logging_setup.py` | `JsonFormatter` and `configure_logging`. |
| `src/pci_scope/interfaces/merchant_app.py` | `logger.info(...)` with ids and statuses only. |
| `src/pci_scope/interfaces/naive_app.py` | A `FileHandler` and the line that logs the whole form. |
| `src/pci_scope/interfaces/servers.py` | Silences Werkzeug's access log. |

## How it works underneath

`logging.getLogger("merchant")` returns the logger of that name. A record travels to the handlers; `StreamHandler(sys.stdout)` writes
to standard output (which Docker collects), `FileHandler(path)` appends to a file. `record.getMessage()` fills the `%s` placeholders.
`logger.propagate = False` stops a record from also going to the root logger's handlers.

## Walkthrough of this repository's use

`src/pci_scope/infrastructure/logging_setup.py`:

```python
_SAFE_FIELDS = ("method", "path", "status", "duration_ms")
```

`src/pci_scope/infrastructure/logging_setup.py`:

```python
class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render a record; only the whitelisted extra fields are included."""
        document = {
            "time": datetime.fromtimestamp(record.created, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        document.update({name: getattr(record, name) for name in _SAFE_FIELDS if hasattr(record, name)})
        return json.dumps(document)
```

The formatter writes time, level, logger and message, plus **only** the whitelisted extra fields.

`src/pci_scope/interfaces/naive_app.py`:

```python
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger = logging.getLogger(f"naive.{log_path}")
    logger.setLevel(logging.INFO)
    logger.handlers[:] = [handler]
```

The naive app gets its own logger writing to a file (`propagate = False` keeps it away from the other handlers).

`src/pci_scope/interfaces/naive_app.py`:

```python
        logger.info("payment request: %s", dict(request.form))  # the mistake: card data reaches the log
```

**The mistake on purpose**: `dict(request.form)` contains `card_number` and `cvv`, and they land in the log. The scanner finds them
there (`evidence/proof-before.txt`).

`src/pci_scope/interfaces/merchant_app.py`:

```python
        logger.info("created payment %s amount=1900 eur", started.intent_id)
```

The redesigned app logs an id and an amount: no body, no card fields.

`src/pci_scope/interfaces/servers.py`:

```python
        logging.getLogger("werkzeug").setLevel(
            logging.WARNING
        )  # no access log: a URL is one more place for data to land
```

Werkzeug's development server logs every request URL. A URL is one more place for data to land, so the access log is turned down.

## Try it yourself

```bash
.venv/bin/python - <<'EOF'
import logging
from pci_scope.infrastructure.logging_setup import configure_logging
configure_logging("INFO")
logging.getLogger("merchant").info("created payment pi_x", extra={"method": "POST", "status": 200, "cvv": "123"})
EOF
```
Prints one JSON line with `time`, `level`, `logger`, `message`, `method`, `status`. The extra `cvv` field is **not** printed.

```bash
cat evidence/proof-before.txt | head -8
```
Shows the scan of the naive checkout's log: card numbers and card fields found (masked).

```bash
cat evidence/proof-after.txt | head -8
```
Shows the scan after the redesign: nothing found.

```bash
.venv/bin/python -c "import logging; print(logging.getLevelName(20))"
```
Prints `INFO`.

## Mistakes people make

- **Logging a request body or a URL with data in it.** That is the leak this repository exists to demonstrate.
- **Forgetting `propagate = False`**, so one record is written twice.
- **Leaving an access log on** that records full URLs.
- **Logging at DEBUG in production.**

## Check yourself

1. What does the naive app log that makes it unsafe?
   **Answer:** `dict(request.form)`, which includes the card number and CVV.
2. Why are log fields whitelisted?
   **Answer:** A field that is not on the list can never leak.
3. What does `propagate = False` do?
   **Answer:** Stops a logger's records from also going to its parents' handlers.
4. Where do the redesigned apps' logs go?
   **Answer:** Standard output.
5. Why is Werkzeug's access log turned down?
   **Answer:** URLs can carry data.

## Further reading

- `logging` (Python 3.12): <https://docs.python.org/3.12/library/logging.html>
- Logging HOWTO: <https://docs.python.org/3.12/howto/logging.html>
