# The Python standard library modules this repository imports

## What it is

The **standard library** is the set of modules that come with Python itself. You `import` them; nothing is downloaded. This note
covers the smaller modules together. The bigger ones have their own notes: `dataclasses.md`, `re.md`, `argparse.md`, `pathlib.md`,
`json.md`, `logging.md`, `urllib.md`, `threads-and-sockets.md` (threading, socket), `hmac-and-hashing.md`, `sqlite.md`, `tomllib.md`.

## Why this repository uses it

The apps need very little beyond what Python ships: HTTP clients, hashing, SQLite, JSON. Two packages are added for the web (Flask) and
the production server (gunicorn).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `typing.Protocol`, `Any` | The interfaces in `application/ports.py` and loosely typed JSON bodies. |
| `collections.abc` | `Callable`, `Mapping`, `Iterator`, `Sequence` in type hints. |
| `contextlib` | `contextmanager`, `closing` (SQLite) and `suppress` (webhook delivery). |
| `types` | `TracebackType` in the type hints of `LocalServer.__exit__`. |
| `time` | `time.time()` for webhook timestamps, `time.sleep` for retry back-off. |
| `secrets` | Random ids and client secrets in the provider. |
| `os`, `sys`, `shutil`, `subprocess` | Environment, error stream; copying and running things in the demo and the tests. |

## How it works underneath

A standard-library module is a file (or folder) inside Python's own installation. `import contextlib` finds it the same way as any
module, through `sys.path`. Their behavior is fixed by the Python version, which is why this repository pins 3.12 as the lowest version.

## Walkthrough of this repository's use

### `typing.Protocol`

`src/pci_scope/application/ports.py`:

```python
class PaymentProvider(Protocol):
    """The payment provider's server-side API. Card numbers never pass through it: the browser sends them elsewhere."""

    def create_customer(self) -> str:
        """A customer token (`cus_...`)."""
        ...

    def create_intent(self, amount_cents: int, currency: str, customer_id: str, save_card: bool) -> Intent:
        """A payment intent whose client secret the browser confirms with the provider."""
        ...

    def retrieve_intent(self, intent_id: str) -> Intent:
```

A `Protocol` says "anything that has these methods will do". `HttpProvider` fits it, and so does a fake in a test, without inheriting
from anything. The `...` body means "no code, only the shape". mypy checks the match. This is how the checkout use case talks to the
provider without importing the HTTP code.

### `contextlib.suppress`

`src/pci_scope/interfaces/provider_app.py`:

```python
    def emit(kind: str, intent: dict[str, Any]) -> None:
        event = {"id": _id("evt"), "type": kind, "data": {"object": _public(intent)}}
        state.events.append(event)
        body = json.dumps(event).encode()
        # If the merchant is down the event is lost; a real provider retries for days.
        with contextlib.suppress(urllib.error.URLError, OSError, TimeoutError):
            state.deliver(state.webhook_url, body, sign(state.webhook_secret, body, int(time.time())))
```

`with contextlib.suppress(urllib.error.URLError, OSError, TimeoutError):` runs the block and **ignores** those errors. A webhook that
cannot be delivered is lost (the comment says why: a real provider retries for days; this stand-in does not), but it must never break
the payment itself.

### `secrets`

`src/pci_scope/interfaces/provider_app.py`:

```python
def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(12)}"
```

`secrets.token_hex(12)` gives 24 random hex characters, so ids like `pi_a1ce9a370c7b1637c72cfbd3` cannot be guessed. (Use `secrets`, not
`random`, for anything security-related.)

### `types.TracebackType` and the context-manager protocol

`src/pci_scope/interfaces/servers.py`:

```python
    def __enter__(self) -> LocalServer:
        self._thread.start()
        return self

    def __exit__(
        self, kind: type[BaseException] | None, value: BaseException | None, trace: TracebackType | None
    ) -> None:
        self._server.shutdown()
        self._thread.join(timeout=5)
        self._server.server_close()
```

A class with `__enter__` and `__exit__` can be used after `with`. `__exit__` receives the error type, value and traceback (or `None`
for each when the block ended well); here it stops the server and joins its thread whatever happened.

### `time`

`src/pci_scope/interfaces/merchant_app.py`:

```python
    def webhook() -> Response:
        outcome = checkout.handle_event(request.get_data(), request.headers.get("Provider-Signature"), int(time.time()))
        logger.info("webhook %s", outcome)
        return jsonify(outcome=outcome)
```

`int(time.time())` is the current time in whole seconds since 1970. The webhook check compares it with the signed timestamp.

## Try it yourself

```bash
.venv/bin/python -c "import secrets; print(secrets.token_hex(12), len(secrets.token_hex(12)))"
```
Prints a random 24-character string and `24`.

```bash
.venv/bin/python -c "import contextlib;
with contextlib.suppress(ZeroDivisionError):
    1 / 0
print('still running')"
```
Prints `still running`: the error was suppressed.

```bash
.venv/bin/python -c "import time; print(int(time.time()) > 1_700_000_000)"
```
Prints `True`.

```bash
.venv/bin/python -c "import sys; print(sys.stdlib_module_names >= {'contextlib', 'secrets', 'threading', 'socket', 'sqlite3', 'urllib'})"
```
Prints `True`: all of them ship with Python.

```bash
grep -rhE "^(import|from) [a-z_.]+" src --include='*.py' | grep -v pci_scope | sort | uniq -c | sort -rn | head -12
```
Lists the imports of the source with counts; only `flask` and `werkzeug` come from outside the standard library.

## Mistakes people make

- **Using `random` for tokens.** Use `secrets`.
- **Suppressing errors silently where they matter.** `suppress` is used once, for a webhook whose loss is documented.
- **Naming your own file like a standard module** (`secrets.py`, `types.py`), which hides the real one.
- **Treating a Protocol as a base class.** It only describes a shape.

## Check yourself

1. What does `contextlib.suppress(X)` do?
   **Answer:** Runs the block and ignores errors of type X.
2. Why `secrets.token_hex` and not `random`?
   **Answer:** `secrets` is built for unguessable values.
3. What are `__enter__` and `__exit__`?
   **Answer:** The methods that make an object usable after `with`.
4. What does a `Protocol` describe?
   **Answer:** The methods an object must have, without inheritance.
5. What is `time.time()`?
   **Answer:** The current time in seconds since 1970.

## Further reading

- Python 3.12 standard library: <https://docs.python.org/3.12/library/index.html>
- `contextlib`: <https://docs.python.org/3.12/library/contextlib.html>; `secrets`: <https://docs.python.org/3.12/library/secrets.html>; `typing.Protocol`: <https://docs.python.org/3.12/library/typing.html#typing.Protocol>; `types`: <https://docs.python.org/3.12/library/types.html>
