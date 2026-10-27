# Python 3.12 (the language)

## What it is

Python is a programming language. You write instructions in plain text files that end in `.py`; a program called
the **interpreter** reads them and does what they say. A **module** is one `.py` file. A **package** is a folder of
modules with an `__init__.py` file. A **function** is a named block of instructions (`def name(...):`). A **class** is
a blueprint for objects that bundle data and functions.

This repository needs Python 3.12 or newer (`requires-python = ">=3.12"`); it is developed and tested on 3.13 and
runs on 3.12 in CI.

## Why this repository uses it

Python reads almost like English, which suits a project whose point is to explain a security design in words and to prove it with checks. Its standard library covers HTTP clients, hashing, SQLite and JSON; the programs add only Flask (web apps) and gunicorn (the production server).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/domain/` | The rules: card patterns and the Luhn check, tokens, webhook signatures, the scope calculator, HAR analysis, evidence checks. Standard library only. |
| `src/pci_scope/application/` | The checkout use cases, the proof (scan) and the evidence pack, and `ports.py`. |
| `src/pci_scope/infrastructure/` | Adapters: SQLite orders, the provider over HTTP, settings, files, logging. |
| `src/pci_scope/interfaces/` | The three Flask apps (`merchant`, `provider`, `naive`), the scripted browser, the demo, servers, the `pci-scope` command line. |
| `tests/` | pytest tests, also Python. |

## How it works underneath

1. You run `python file.py` (or a command created from it). The interpreter turns the text into **bytecode**
   (simple instructions) and runs them one by one.
2. Names point to objects. `x = 3` makes the name `x` point to the number 3.
3. `import a.b` finds the file `a/b.py` in the folders listed in `sys.path`, runs it once, and keeps it in memory
   for any later import.
4. Indentation (four spaces) groups lines into blocks. There are no braces.
5. Errors are **exceptions**. `raise SomeError("message")` stops the current function and goes up the call chain
   until a `try ... except` handles it, or the program ends with a traceback.
6. **Type hints** (`x: int`) are notes for people and tools; the interpreter ignores them. See `mypy.md`.

## Walkthrough of this repository's use

### A module and its docstring

`src/pci_scope/domain/findings.py`:

```python
"""A problem a check found, with a code so a test and a reader can point at the rule."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """One rule violation: the rule's code, what it is about, and what is wrong."""

    code: str
    subject: str
    message: str
```

- The triple-quoted text at the top is the module's **docstring**; ruff requires one on every public module, class and function.
- `from __future__ import annotations` makes type hints lazy text.
- `@dataclass(frozen=True)` is explained in `dataclasses.md`.
- `def error(code: str, subject: str, message: str) -> Finding:` takes three pieces of text and returns a `Finding`. `code: str` is a
  **type hint**: a note for people and for mypy; Python does not enforce it.

### Errors are classes, and a regular expression guards a value

`src/pci_scope/domain/payment.py`:

```python
TOKEN = re.compile(r"^(pi|pm|cus|re)_[A-Za-z0-9]{8,64}$")
PAYMENT_STATUSES = ("pending", "succeeded", "failed", "refunded")
```

`src/pci_scope/domain/payment.py`:

```python
class PaymentError(Exception):
    """A payment failed in a way the customer should hear about (declined, unknown token, provider down)."""


def is_token(value: str) -> bool:
    """True for a provider id such as `pi_...` or `pm_...`: the only payment values the merchant may store."""
```

- `class PaymentError(Exception)` defines a new kind of error that **inherits** from `Exception`. `raise PaymentError("...")` stops the
  current function; a `try ... except` further up decides what to do. The merchant app turns it into an HTTP `402` answer.
- `is_token` returns `bool(TOKEN.match(value))`: `match` returns a match object or `None`, and `bool(...)` turns that into `True` or
  `False`. This is the only gate between the outside world and the database: a value that is not a provider token is refused.

### A function that returns a function, and retries

`src/pci_scope/infrastructure/provider_http.py`:

```python
    def _call(self, method: str, path: str, body: bytes | None) -> dict[str, Any]:
        request = urllib.request.Request(
            self._base + path,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        delay = 0.2
        for attempt in range(1, ATTEMPTS + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    return dict(json.loads(response.read()))
            except urllib.error.HTTPError as problem:
                if problem.code < 500:
                    raise PaymentError(_message(problem)) from None
                if attempt == ATTEMPTS:
                    raise PaymentError("the payment provider is failing") from None
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt == ATTEMPTS:
                    raise PaymentError("the payment provider is unreachable") from None
            self._sleep(delay)
            delay *= 2
        raise AssertionError("unreachable")  # pragma: no cover
```

- A **loop with retries**: `for attempt in range(1, ATTEMPTS + 1)` tries up to three times.
- `except urllib.error.HTTPError as problem:` catches one kind of failure and names it; `problem.code < 500` is the HTTP status
  (a 4xx is the answer, a 5xx is retried).
- `raise PaymentError(...) from None` raises the program's own error and hides the library's traceback.
- `with urllib.request.urlopen(...) as response:` closes the connection at the end of the block.
- `self._sleep(delay); delay *= 2` waits and doubles the wait (exponential back-off). `sleep` is a parameter, so tests can replace it.

### Conditional expressions and unpacking

`src/pci_scope/application/checkout.py`:

```python
def _status(intent: Intent) -> str:
    return (
        "succeeded"
        if intent.status == "succeeded"
        else "failed"
        if intent.status in ("requires_payment_method", "canceled")
        else "pending"
    )
```

A chain of **conditional expressions**: `A if condition else B`. The provider's status becomes the merchant's own: `succeeded`,
`failed` or `pending`.

`src/pci_scope/domain/webhook.py`:

```python
    parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
```

`dict(item.split("=", 1) for item in header.split(",") if "=" in item)` builds a dictionary from a header like
`t=1700000000,v1=abcd`: split on commas, keep pieces with `=`, split each into a key and a value at the first `=`.

### The entry point

`src/pci_scope/interfaces/cli.py`:

```python
def main(argv: Sequence[str] | None = None) -> int:
    """Run one command and return the exit code."""
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings(os.environ)
        configure_logging(settings.log_level)
        return _run(args, settings)
    except (SettingsError, CatalogError) as problem:
        print(f"configuration error: {problem}", file=sys.stderr)
```

`src/pci_scope/interfaces/cli.py`:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

`__name__` is `"__main__"` only when the file is run directly. `SystemExit(code)` ends the program with that exit status.

## Try it yourself

```bash
.venv/bin/python --version
```
Prints the interpreter version (`Python 3.13.x`).

```bash
.venv/bin/python -c "from pci_scope.domain.payment import is_token; print(is_token('pi_a1ce9a370c7b1637c72cfbd3'), is_token('4242424242424242'))"
```
Prints `True False`: a payment-intent token passes; a card number does not.

```bash
.venv/bin/python -c "from pci_scope.domain.webhook import sign, verify; h = sign('s' * 32, b'{}', 1000); print(h[:8], verify('s' * 32, b'{}', h, 1100), verify('s' * 32, b'{}', h, 9999))"
```
Prints `t=1000,v` then `True False`: valid within the tolerance, refused when too old.

```bash
.venv/bin/python -c "from pci_scope.domain.payment import PaymentError; print(issubclass(PaymentError, Exception))"
```
Prints `True`.

```bash
.venv/bin/python -c "print([n * n for n in range(5) if n % 2 == 0])"
```
Prints `[0, 4, 16]`: a list comprehension.

## Mistakes people make

- **Mixing tabs and spaces** for indentation. `.editorconfig` and `ruff format` prevent it.
- **Changing a list while looping over it.**
- **Using `==` to compare with `None`.** Use `is None`.
- **Mutable default arguments** (`def f(x=[])`). Ruff's `B` rules catch this.
- **Catching every error** with a bare `except:` and hiding bugs. This code catches the one named error it expects.

## Check yourself

1. What does `from __future__ import annotations` do?
   **Answer:** It makes type hints lazy text, so they need not be evaluable at load time.
2. What does `raise X from None` do?
   **Answer:** It raises a new error without showing the original one as its cause.
3. What does `@property` allow?
   **Answer:** Calling a method like an attribute, without parentheses.
4. What is `__name__ == "__main__"` for?
   **Answer:** To run code only when the file is started directly, not when imported.
5. What does `(m := pattern.match(line))` do in an `if`?
   **Answer:** It stores the match in `m` and tests whether there was one.

## Further reading

- Python 3.12 tutorial: <https://docs.python.org/3.12/tutorial/>
- Language reference: <https://docs.python.org/3.12/reference/>
- What's new in 3.12: <https://docs.python.org/3.12/whatsnew/3.12.html>
