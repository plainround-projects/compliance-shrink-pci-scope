# Interfaces layer code

## What it is

The entry points: the command line, the web routes and the wiring that builds everything from settings. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

This is where the repository's interfaces work happens. Reading it file by file, with every line explained, is how a reader sees the work that was done.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/__init__.py` | 1 lines. The three web apps, the browser simulator and the command line. Nothing depends on this package. |
| `src/pci_scope/interfaces/browser_sim.py` | 100 lines. A scripted browser: it makes the requests a customer's browser makes during a checkout and records them as a … |
| `src/pci_scope/interfaces/cli.py` | 118 lines. `pci-scope`: the scenario, the scope, the scanner, the verification. Exit codes: 0 ok, 1 findings, 2 bad inpu… |
| `src/pci_scope/interfaces/demo.py` | 185 lines. The lesson's scenario against real local servers, ending in the evidence pack. |
| `src/pci_scope/interfaces/factories.py` | 36 lines. Application factories for gunicorn: `gunicorn "pci_scope.interfaces.factories:merchant()"`. |
| `src/pci_scope/interfaces/merchant_app.py` | 108 lines. The merchant's web app after the redesign: it serves the page, creates the payment, asks the provider the res… |
| `src/pci_scope/interfaces/naive_app.py` | 28 lines. The "before": the lesson's naive checkout. It posts card details to its own server and logs the whole form. |
| `src/pci_scope/interfaces/provider_app.py` | 228 lines. A local stand-in for a payment provider's test mode: the same shape of API as a real one, with hosted fields. |
| `src/pci_scope/interfaces/servers.py` | 31 lines. Run the three apps as real HTTP servers on local ports, in threads, and stop them cleanly. |

## How it works underneath

This outermost layer turns requests (a typed command, an HTTP call) into use-case calls and turns errors into exit codes or status codes. It is also where the adapters are created and connected (the composition root). Nothing depends on it.

## Walkthrough of this repository's use

### `src/pci_scope/interfaces/__init__.py`

`src/pci_scope/interfaces/__init__.py` lines 1 to 1:

```python
"""The three web apps, the browser simulator and the command line. Nothing depends on this package."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** The three web apps, the browser simulator and the command line. Nothing depends on this package.

### `src/pci_scope/interfaces/browser_sim.py`

`src/pci_scope/interfaces/browser_sim.py` lines 1 to 19:

```python
"""A scripted browser: it makes the requests a customer's browser makes during a checkout and records them as a HAR.

It does not run JavaScript. It reads the merchant's page, then makes the requests that page's scripts make: load the
provider's script, ask the merchant for a payment, load the provider's card frame, send the card to the provider,
confirm the payment, return to the merchant. Everything goes over real HTTP to real servers.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from pci_scope.domain.card import TEST_CARD, card_field_names
from pci_scope.domain.har import Exchange
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** A scripted browser: it makes the requests a customer's browser makes during a checkout and records them as a HAR. It does not run JavaScript. It reads the merchant's page, then makes the requests that page's scripts make: load the provider's script, ask the merchant for a payment, load the provider's card frame, send the card to the provider, confirm the payment, return to the merchant. Everythin…

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- It imports module `re`.
- It imports module `urllib.error`.
- It imports module `urllib.parse`.
- It imports module `urllib.request`.
- From `dataclasses` it takes `dataclass, field`.
- From `typing` it takes `Any`.
- From `pci_scope.domain.card` it takes `TEST_CARD, card_field_names`.
- From `pci_scope.domain.har` it takes `Exchange`.

`src/pci_scope/interfaces/browser_sim.py` lines 22 to 28:

```python
@dataclass(frozen=True)
class Reply:
    """What came back."""

    status: int
    headers: dict[str, str]
    body: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Reply`**. What came back. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `status`: a `int`.
- Field `headers`: a `dict[str, str]`.
- Field `body`: a `str`.

`src/pci_scope/interfaces/browser_sim.py` lines 31 to 41:

```python
@dataclass
class PaymentRun:
    """The requests made, and what the page and the payment turned out to be."""

    exchanges: list[Exchange] = field(default_factory=list)
    intent_id: str = ""
    final_text: str = ""
    final_status: int = 0
    page_headers: dict[str, str] = field(default_factory=dict)
    page_card_fields: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
```

**Class `PaymentRun`**. The requests made, and what the page and the payment turned out to be. Decorators: `@dataclass`.

Its parts:

- Field `exchanges`: a `list[Exchange]`, default `field(default_factory=list)`.
- Field `intent_id`: a `str`, default `''`.
- Field `final_text`: a `str`, default `''`.
- Field `final_status`: a `int`, default `0`.
- Field `page_headers`: a `dict[str, str]`, default `field(default_factory=dict)`.
- Field `page_card_fields`: a `list[str]`, default `field(default_factory=list)`.
- Field `scripts`: a `list[str]`, default `field(default_factory=list)`.

`src/pci_scope/interfaces/browser_sim.py` lines 44 to 45:

```python
class Browser:
    """Makes HTTP requests and keeps the log of them."""
```

**Class `Browser`**. Makes HTTP requests and keeps the log of them.

`src/pci_scope/interfaces/browser_sim.py` lines 47 to 49:

```python
    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout
        self.exchanges: list[Exchange] = []
```

**Method `__init__` of class `Browser`.**

It takes: `timeout` (a `float`), default `10.0`.

It gives back a `None`.

Step by step:

- Stores `timeout` in `self._timeout`.
- Declares `self.exchanges` as a `list[Exchange]` and stores the list `[]` in it.

`src/pci_scope/interfaces/browser_sim.py` lines 51 to 79:

```python
    def request(
        self,
        method: str,
        url: str,
        form: dict[str, str] | None = None,
        payload: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Reply:
        """One request; HTTP errors are replies, not exceptions."""
        body: bytes | None = None
        sent = dict(headers or {})
        if form is not None:
            body = urllib.parse.urlencode(form).encode()
            sent["Content-Type"] = "application/x-www-form-urlencoded"
        elif payload is not None:
            body = json.dumps(payload).encode()
            sent["Content-Type"] = "application/json"
        elif method == "POST":
            body = b""
        http = urllib.request.Request(url, data=body, method=method, headers=sent)
        try:
            with urllib.request.urlopen(http, timeout=self._timeout) as response:
                reply = Reply(
                    response.status, dict(response.headers), response.read().decode("utf-8", errors="replace")
                )
        except urllib.error.HTTPError as problem:
            reply = Reply(problem.code, dict(problem.headers), problem.read().decode("utf-8", errors="replace"))
        self.exchanges.append(Exchange(method, url, reply.status, (body or b"").decode()))
        return reply
```

> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Method `request` of class `Browser`.** One request; HTTP errors are replies, not exceptions.

It takes: `method` (a `str`); `url` (a `str`); `form` (a `dict[str, str] | None`), default `None`; `payload` (a `Any`), default `None`; `headers` (a `dict[str, str] | None`), default `None`.

It gives back a `Reply`.

Step by step:

- Declares `body` as a `bytes | None` and stores nothing (`None`) in it.
- Stores the result of calling `dict(headers or {})` in `sent`.
- If `form` is not the same object as `None`:
  - Stores the result of calling `urllib.parse.urlencode(form).encode()` in `body`.
  - Stores the text `'application/x-www-form-urlencoded'` in `sent['Content-Type']`.
- Otherwise, if `payload` is not the same object as `None`:
  - Stores the result of calling `json.dumps(payload).encode()` in `body`.
  - Stores the text `'application/json'` in `sent['Content-Type']`.
- Otherwise, if `method` equals `'POST'`:
  - Stores the number `b''` in `body`.
- Stores the result of calling `urllib.request.Request(url, data=body, method=method, headers=sent)` in `http`.
- Tries:
  - Inside a `with` block that opens `urllib.request.urlopen(http, timeout=self._timeout)` (named `response`):
    - Stores the result of calling `Reply(response.status, dict(response.headers), response.read().decode('utf-8', errors='re…` in `reply`.
- If `urllib.error.HTTPError` happens (named `problem`):
  - Stores the result of calling `Reply(problem.code, dict(problem.headers), problem.read().decode('utf-8', errors='replace…` in `reply`.
- Calls `self.exchanges.append(Exchange(method, url, reply.status, (body or b'').decode()))`.
- Gives back `reply`.

`src/pci_scope/interfaces/browser_sim.py` lines 82 to 113:

```python
def pay_with_hosted_fields(
    browser: Browser, merchant: str, provider: str, publishable_key: str, card: str = TEST_CARD
) -> PaymentRun:
    """The redesigned checkout, start to finish, with the published test card typed into the provider's frame."""
    run = PaymentRun()
    page = browser.request("GET", f"{merchant}/")
    run.page_headers = page.headers
    run.page_card_fields = card_field_names(page.body)
    run.scripts = re.findall(r'<script src="([^"]+)"', page.body)
    browser.request("GET", f"{merchant}/static/checkout.js")
    browser.request("GET", f"{provider}/v1/elements.js")
    started = json.loads(browser.request("POST", f"{merchant}/create-payment").body)
    run.intent_id = started["id"]
    secret = urllib.parse.quote(started["clientSecret"])
    browser.request("GET", f"{provider}/frame?origin={urllib.parse.quote(merchant)}&client_secret={secret}")
    key = {"X-Publishable-Key": publishable_key}
    method = json.loads(
        browser.request(
            "POST",
            f"{provider}/v1/payment_methods",
            form={"card[number]": card, "card[exp_month]": "12", "card[exp_year]": "30", "card[cvc]": "123"},
            headers=key,
        ).body
    )
    browser.request(
        "POST", f"{provider}/v1/payment_intents/{run.intent_id}/confirm",
        form={"client_secret": started["clientSecret"], "payment_method": method["id"]}, headers=key,
    )  # fmt: skip
    final = browser.request("GET", f"{merchant}/done?payment_intent={run.intent_id}")
    run.final_text, run.final_status = final.body, final.status
    run.exchanges = list(browser.exchanges)
    return run
```

> **In plain words.** A **regular expression** is a short pattern for text, such as `^## (.+)$` for "a line starting with ## ". `re.compile` prepares it once; `.match` tries it at the start of a string and returns a match object or `None`.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `pay_with_hosted_fields`.** The redesigned checkout, start to finish, with the published test card typed into the provider's frame.

It takes: `browser` (a `Browser`); `merchant` (a `str`); `provider` (a `str`); `publishable_key` (a `str`); `card` (a `str`), default `TEST_CARD`.

It gives back a `PaymentRun`.

Step by step:

- Stores the result of calling `PaymentRun()` in `run`.
- Stores the result of calling `browser.request('GET', f'{merchant}/')` in `page`.
- Stores `page.headers` in `run.page_headers`.
- Stores the result of calling `card_field_names(page.body)` in `run.page_card_fields`.
- Stores the result of calling `re.findall('<script src="([^"]+)"', page.body)` in `run.scripts`.
- Calls `browser.request('GET', f'{merchant}/static/checkout.js')`.
- Calls `browser.request('GET', f'{provider}/v1/elements.js')`.
- Stores the result of calling `json.loads(browser.request('POST', f'{merchant}/create-payment').body)` in `started`.
- Stores `started['id']` in `run.intent_id`.
- Stores the result of calling `urllib.parse.quote(started['clientSecret'])` in `secret`.
- Calls `browser.request('GET', f'{provider}/frame?origin={urllib.parse.quote(merchant)}&client_secret={secret}')`.
- Stores the dictionary `{'X-Publishable-Key': publishable_key}` in `key`.
- Stores the result of calling `json.loads(browser.request('POST', f'{provider}/v1/payment_methods', form={'card[number]'…` in `method`.
- Calls `browser.request('POST', f'{provider}/v1/payment_intents/{run.intent_id}/confirm', form={'client_secret': star…`.
- Stores the result of calling `browser.request('GET', f'{merchant}/done?payment_intent={run.intent_id}')` in `final`.
- Unpacks the tuple `(final.body, final.status)` into `(run.final_text, run.final_status)`.
- Stores the result of calling `list(browser.exchanges)` in `run.exchanges`.
- Gives back `run`.

`src/pci_scope/interfaces/browser_sim.py` lines 116 to 118:

```python
def pay_on_naive_checkout(browser: Browser, naive: str, card: str = TEST_CARD) -> Reply:
    """The "before": the card posted to the merchant's own server."""
    return browser.request("POST", f"{naive}/pay", form={"card_number": card, "expiry": "12/30", "cvv": "123"})
```

**Function `pay_on_naive_checkout`.** The "before": the card posted to the merchant's own server.

It takes: `browser` (a `Browser`); `naive` (a `str`); `card` (a `str`), default `TEST_CARD`.

It gives back a `Reply`.

Step by step:

- Gives back the result of calling `browser.request('POST', f'{naive}/pay', form={'card_number': card, 'expiry': '12/30', 'cv…`.

### `src/pci_scope/interfaces/cli.py`

`src/pci_scope/interfaces/cli.py` lines 1 to 28:

```python
"""`pci-scope`: the scenario, the scope, the scanner, the verification. Exit codes: 0 ok, 1 findings, 2 bad input."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlsplit

from werkzeug.serving import run_simple

from pci_scope.application.checkout import CheckoutService
from pci_scope.application.pack import scope_documents
from pci_scope.application.proof import run_scan
from pci_scope.domain.evidence import verify_pack
from pci_scope.infrastructure.artifacts import PathArtifacts
from pci_scope.infrastructure.catalog import CatalogError, load_inventory, load_requirements
from pci_scope.infrastructure.evidence_store import FileEvidenceStore
from pci_scope.infrastructure.logging_setup import configure_logging
from pci_scope.infrastructure.provider_http import HttpProvider
from pci_scope.infrastructure.settings import Settings, SettingsError, load_settings
from pci_scope.infrastructure.sqlite_orders import SqliteOrders
from pci_scope.interfaces.demo import run_demo
from pci_scope.interfaces.merchant_app import create_merchant_app
from pci_scope.interfaces.naive_app import create_naive_app
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** `pci-scope`: the scenario, the scope, the scanner, the verification. Exit codes: 0 ok, 1 findings, 2 bad input.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `argparse`.
- It imports module `os`.
- It imports module `sys`.
- From `collections.abc` it takes `Sequence`.
- From `pathlib` it takes `Path`.
- From `urllib.parse` it takes `urlsplit`.
- From `werkzeug.serving` it takes `run_simple`.
- From `pci_scope.application.checkout` it takes `CheckoutService`.
- From `pci_scope.application.pack` it takes `scope_documents`.
- From `pci_scope.application.proof` it takes `run_scan`.
- From `pci_scope.domain.evidence` it takes `verify_pack`.
- From `pci_scope.infrastructure.artifacts` it takes `PathArtifacts`.
- From `pci_scope.infrastructure.catalog` it takes `CatalogError, load_inventory, load_requirements`.
- From `pci_scope.infrastructure.evidence_store` it takes `FileEvidenceStore`.
- From `pci_scope.infrastructure.logging_setup` it takes `configure_logging`.
- From `pci_scope.infrastructure.provider_http` it takes `HttpProvider`.
- From `pci_scope.infrastructure.settings` it takes `Settings, SettingsError, load_settings`.
- From `pci_scope.infrastructure.sqlite_orders` it takes `SqliteOrders`.
- From `pci_scope.interfaces.demo` it takes `run_demo`.
- From `pci_scope.interfaces.merchant_app` it takes `create_merchant_app`.
- From `pci_scope.interfaces.naive_app` it takes `create_naive_app`.
- From `pci_scope.interfaces.provider_app` it takes `ProviderState, create_provider_app`.

`src/pci_scope/interfaces/cli.py` lines 30 to 30:

```python
ROOT = Path()
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `Path()` in `ROOT`.

`src/pci_scope/interfaces/cli.py` lines 33 to 49:

```python
def build_parser() -> argparse.ArgumentParser:
    """One subcommand per job."""
    parser = argparse.ArgumentParser(prog="pci-scope", description="Shrink the PCI scope of a checkout and prove it.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="run the whole scenario and write the evidence pack")
    commands.add_parser(
        "verify", help="check that every requirement maps to evidence and every file says what it should"
    )
    commands.add_parser("scope", help="print the scope before and after, and what changed")
    scan = commands.add_parser(
        "scan", help="search files and folders for card numbers and card fields; exit 1 if any are found"
    )
    scan.add_argument("paths", nargs="+", type=Path)
    serve = commands.add_parser("serve", help="run one app on its configured port")
    serve.add_argument("app", choices=("provider", "merchant", "naive"))
    commands.add_parser("db", help="create the merchant's database from sql/001_schema.sql and 002_seed.sql")
    return parser
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Function `build_parser`.** One subcommand per job.

It gives back a `argparse.ArgumentParser`.

Step by step:

- Stores the result of calling `argparse.ArgumentParser(prog='pci-scope', description='Shrink the PCI scope of a checkout…` in `parser`.
- Stores the result of calling `parser.add_subparsers(dest='command', required=True)` in `commands`.
- Calls `commands.add_parser('demo', help='run the whole scenario and write the evidence pack')`.
- Calls `commands.add_parser('verify', help='check that every requirement maps to evidence and every file says what it…`.
- Calls `commands.add_parser('scope', help='print the scope before and after, and what changed')`.
- Stores the result of calling `commands.add_parser('scan', help='search files and folders for card numbers and card fiel…` in `scan`.
- Calls `scan.add_argument('paths', nargs='+', type=Path)`.
- Stores the result of calling `commands.add_parser('serve', help='run one app on its configured port')` in `serve`.
- Calls `serve.add_argument('app', choices=('provider', 'merchant', 'naive'))`.
- Calls `commands.add_parser('db', help="create the merchant's database from sql/001_schema.sql and 002_seed.sql")`.
- Gives back `parser`.

`src/pci_scope/interfaces/cli.py` lines 52 to 64:

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
        return 2
    except OSError as problem:
        print(f"error: {problem}", file=sys.stderr)
        return 2
```

> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `main`.** Run one command and return the exit code.

It takes: `argv` (a `Sequence[str] | None`), default `None`.

It gives back a `int`.

Step by step:

- Stores the result of calling `build_parser().parse_args(argv)` in `args`.
- Tries:
  - Stores the result of calling `load_settings(os.environ)` in `settings`.
  - Calls `configure_logging(settings.log_level)`.
  - Gives back the result of calling `_run(args, settings)`.
- If `(SettingsError, CatalogError)` happens (named `problem`):
  - Calls `print(f'configuration error: {problem}', file=sys.stderr)`.
  - Gives back the number `2`.
- If `OSError` happens (named `problem`):
  - Calls `print(f'error: {problem}', file=sys.stderr)`.
  - Gives back the number `2`.

`src/pci_scope/interfaces/cli.py` lines 67 to 92:

```python
def _run(args: argparse.Namespace, settings: Settings) -> int:
    if args.command == "demo":
        result = run_demo(settings, ROOT)
        print(result.before.text, end="")
        print(result.after.text, end="")
        print(f"order statuses: {result.order_statuses}")
        print(f"evidence pack: {', '.join(result.pack_files)}")
        return _verify(settings)
    if args.command == "verify":
        return _verify(settings)
    if args.command == "scope":
        before, after = load_inventory(ROOT / "scope" / "before.toml"), load_inventory(ROOT / "scope" / "after.toml")
        for name, text in scope_documents(before, after).items():
            print(f"== {name}\n{text}")
        return 0
    if args.command == "scan":
        outcome = run_scan("scanning:", PathArtifacts(args.paths))
        print(outcome.text, end="")
        return outcome.exit_code
    if args.command == "db":
        orders = SqliteOrders(settings.database_path)
        schema = (ROOT / "sql" / "001_schema.sql").read_text(encoding="utf-8")
        orders.initialize(schema + (ROOT / "sql" / "002_seed.sql").read_text(encoding="utf-8"))
        print(f"created {settings.database_path}")
        return 0
    return _serve(args.app, settings)
```

> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.

**Function `_run`.**

It takes: `args` (a `argparse.Namespace`); `settings` (a `Settings`).

It gives back a `int`.

Step by step:

- If `args.command` equals `'demo'`:
  - Stores the result of calling `run_demo(settings, ROOT)` in `result`.
  - Calls `print(result.before.text, end='')`.
  - Calls `print(result.after.text, end='')`.
  - Calls `print(f'order statuses: {result.order_statuses}')`.
  - Calls `print(f"evidence pack: {', '.join(result.pack_files)}")`.
  - Gives back the result of calling `_verify(settings)`.
- If `args.command` equals `'verify'`:
  - Gives back the result of calling `_verify(settings)`.
- If `args.command` equals `'scope'`:
  - Unpacks the tuple `(load_inventory(ROOT / 'scope' / 'before.toml'), load_inventory(ROOT …` into `(before, after)`.
  - For each `(name, text)` in the result of calling `scope_documents(before, after).items()`:
    - Calls `print(f'== {name}\n{text}')`.
  - Gives back the number `0`.
- If `args.command` equals `'scan'`:
  - Stores the result of calling `run_scan('scanning:', PathArtifacts(args.paths))` in `outcome`.
  - Calls `print(outcome.text, end='')`.
  - Gives back `outcome.exit_code`.
- If `args.command` equals `'db'`:
  - Stores the result of calling `SqliteOrders(settings.database_path)` in `orders`.
  - Stores the result of calling `(ROOT / 'sql' / '001_schema.sql').read_text(encoding='utf-8')` in `schema`.
  - Calls `orders.initialize(schema + (ROOT / 'sql' / '002_seed.sql').read_text(encoding='utf-8'))`.
  - Calls `print(f'created {settings.database_path}')`.
  - Gives back the number `0`.
- Gives back the result of calling `_serve(args.app, settings)`.

`src/pci_scope/interfaces/cli.py` lines 95 to 105:

```python
def _verify(settings: Settings) -> int:
    requirements, gaps = load_requirements(ROOT / "controls" / "requirements.toml")
    store = FileEvidenceStore(settings.evidence_dir)
    findings = verify_pack(
        requirements, store.manifest(), store.read_all(), gaps, settings.merchant_base_url, settings.provider_base_url
    )
    for finding in findings:
        print(f"{finding.code} {finding.subject}: {finding.message}")
    verdict = "OK" if not findings else "FAILED"
    print(f"{verdict}: {len(requirements)} requirements, {len(store.read_all())} files, {len(findings)} problem(s)")
    return 0 if not findings else 1
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `_verify`.**

It takes: `settings` (a `Settings`).

It gives back a `int`.

Step by step:

- Unpacks the result of calling `load_requirements(ROOT / 'controls' / 'requirements.toml')` into `(requirements, gaps)`.
- Stores the result of calling `FileEvidenceStore(settings.evidence_dir)` in `store`.
- Stores the result of calling `verify_pack(requirements, store.manifest(), store.read_all(), gaps, settings.merchant_bas…` in `findings`.
- For each `finding` in `findings`:
  - Calls `print(f'{finding.code} {finding.subject}: {finding.message}')`.
- Stores `'OK'` if not (`findings`), otherwise `'FAILED'` in `verdict`.
- Calls `print(f'{verdict}: {len(requirements)} requirements, {len(store.read_all())} files, {len(findings)} problem(s…`.
- Gives back `0` if not (`findings`), otherwise `1`.

`src/pci_scope/interfaces/cli.py` lines 108 to 131:

```python
def _serve(app: str, settings: Settings) -> int:
    if app == "provider":
        state = ProviderState(
            settings.secret_key,
            settings.publishable_key,
            settings.webhook_secret,
            f"{settings.merchant_base_url}/webhook",
        )
        flask_app, url = create_provider_app(state), settings.provider_base_url
    elif app == "merchant":
        orders = SqliteOrders(settings.database_path)
        orders.initialize((ROOT / "sql" / "001_schema.sql").read_text(encoding="utf-8"))
        checkout = CheckoutService(
            HttpProvider(settings.provider_base_url, settings.secret_key), orders, settings.webhook_secret
        )
        flask_app, url = (
            create_merchant_app(checkout, settings.provider_public_url, settings.publishable_key),
            settings.merchant_base_url,
        )
    else:
        flask_app, url = create_naive_app(settings.naive_log_path), settings.naive_base_url
    parts = urlsplit(url)
    run_simple(parts.hostname or "127.0.0.1", parts.port or 80, flask_app, threaded=True)
    return 0
```

**Function `_serve`.**

It takes: `app` (a `str`); `settings` (a `Settings`).

It gives back a `int`.

Step by step:

- If `app` equals `'provider'`:
  - Stores the result of calling `ProviderState(settings.secret_key, settings.publishable_key, settings.webhook_secret, f'{…` in `state`.
  - Unpacks the tuple `(create_provider_app(state), settings.provider_base_url)` into `(flask_app, url)`.
- Otherwise, if `app` equals `'merchant'`:
  - Stores the result of calling `SqliteOrders(settings.database_path)` in `orders`.
  - Calls `orders.initialize((ROOT / 'sql' / '001_schema.sql').read_text(encoding='utf-8'))`.
  - Stores the result of calling `CheckoutService(HttpProvider(settings.provider_base_url, settings.secret_key), orders, se…` in `checkout`.
  - Unpacks the tuple `(create_merchant_app(checkout, settings.provider_public_url, settings…` into `(flask_app, url)`.
- Otherwise:
  - Unpacks the tuple `(create_naive_app(settings.naive_log_path), settings.naive_base_url)` into `(flask_app, url)`.
- Stores the result of calling `urlsplit(url)` in `parts`.
- Calls `run_simple(parts.hostname or '127.0.0.1', parts.port or 80, flask_app, threaded=True)`.
- Gives back the number `0`.

`src/pci_scope/interfaces/cli.py` lines 134 to 135:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

> **In plain words.** `if __name__ == "__main__":` runs its steps only when the file is started directly, not when another file imports it.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

This statement:

- If `__name__` equals `'__main__'`:
  - Stops here by raising `SystemExit(main())`.

### `src/pci_scope/interfaces/demo.py`

`src/pci_scope/interfaces/demo.py` lines 1 to 40:

```python
"""The lesson's scenario against real local servers, ending in the evidence pack.

1. The naive checkout takes a test payment and logs the card number: the problem, measured.
2. The redesigned checkout takes a test payment through the provider's hosted fields: the card goes only there.
3. A repeat charge from tokens, a refund and a webhook, to show the merchant needs no card for any of them.
4. The merchant's log, database and backup are scanned, the old route is probed, and everything is written to the pack.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from pci_scope.application.checkout import CheckoutService
from pci_scope.application.pack import (
    render_index,
    render_page_controls,
    render_routes,
    render_token_storage,
    scope_documents,
)
from pci_scope.application.proof import ScanOutcome, run_scan
from pci_scope.domain.har import summarize, to_har
from pci_scope.infrastructure.artifacts import MerchantArtifacts, NaiveArtifacts
from pci_scope.infrastructure.catalog import load_inventory, load_requirements
from pci_scope.infrastructure.evidence_store import FileEvidenceStore
from pci_scope.infrastructure.provider_http import HttpProvider
from pci_scope.infrastructure.settings import Settings
from pci_scope.infrastructure.sqlite_orders import SqliteOrders
from pci_scope.interfaces.browser_sim import Browser, PaymentRun, pay_on_naive_checkout, pay_with_hosted_fields
from pci_scope.interfaces.merchant_app import create_merchant_app
from pci_scope.interfaces.naive_app import create_naive_app
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app
from pci_scope.interfaces.servers import LocalServer
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The lesson's scenario against real local servers, ending in the evidence pack. 1. The naive checkout takes a test payment and logs the card number: the problem, measured. 2. The redesigned checkout takes a test payment through the provider's hosted fields: the card goes only there. 3. A repeat charge from tokens, a refund and a webhook, to show the merchant needs no card for any of them. 4. The m…

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- It imports module `logging`.
- It imports module `shutil`.
- It imports module `subprocess`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `UTC, datetime`.
- From `pathlib` it takes `Path`.
- From `urllib.parse` it takes `urlsplit`.
- From `pci_scope.application.checkout` it takes `CheckoutService`.
- From `pci_scope.application.pack` it takes `render_index, render_page_controls, render_routes, render_token_storage, scope_documents`.
- From `pci_scope.application.proof` it takes `ScanOutcome, run_scan`.
- From `pci_scope.domain.har` it takes `summarize, to_har`.
- From `pci_scope.infrastructure.artifacts` it takes `MerchantArtifacts, NaiveArtifacts`.
- From `pci_scope.infrastructure.catalog` it takes `load_inventory, load_requirements`.
- From `pci_scope.infrastructure.evidence_store` it takes `FileEvidenceStore`.
- From `pci_scope.infrastructure.provider_http` it takes `HttpProvider`.
- From `pci_scope.infrastructure.settings` it takes `Settings`.
- From `pci_scope.infrastructure.sqlite_orders` it takes `SqliteOrders`.
- From `pci_scope.interfaces.browser_sim` it takes `Browser, PaymentRun, pay_on_naive_checkout, pay_with_hosted_fields`.
- From `pci_scope.interfaces.merchant_app` it takes `create_merchant_app`.
- From `pci_scope.interfaces.naive_app` it takes `create_naive_app`.
- From `pci_scope.interfaces.provider_app` it takes `ProviderState, create_provider_app`.
- From `pci_scope.interfaces.servers` it takes `LocalServer`.

`src/pci_scope/interfaces/demo.py` lines 42 to 43:

```python
GREP_PAN = r"4242[ -]?4242[ -]?4242[ -]?4242"
GREP_FIELDS = "cvv|cvc|card_number"
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'4242[ -]?4242[ -]?4242[ -]?4242'` in `GREP_PAN`.
- Stores the text `'cvv|cvc|card_number'` in `GREP_FIELDS`.

`src/pci_scope/interfaces/demo.py` lines 46 to 54:

```python
@dataclass(frozen=True)
class DemoResult:
    """What the scenario produced, for the command line to report."""

    before: ScanOutcome
    after: ScanOutcome
    run: PaymentRun
    order_statuses: dict[str, str]
    pack_files: tuple[str, ...]
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `DemoResult`**. What the scenario produced, for the command line to report. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `before`: a `ScanOutcome`.
- Field `after`: a `ScanOutcome`.
- Field `run`: a `PaymentRun`.
- Field `order_statuses`: a `dict[str, str]`.
- Field `pack_files`: a `tuple[str, ...]`.

`src/pci_scope/interfaces/demo.py` lines 57 to 58:

```python
def _port(url: str) -> int:
    return urlsplit(url).port or 80
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `_port`.**

It takes: `url` (a `str`).

It gives back a `int`.

Step by step:

- Gives back whether `urlsplit(url).port` or `80`.

`src/pci_scope/interfaces/demo.py` lines 61 to 62:

```python
def run_demo(settings: Settings, root: Path = Path()) -> DemoResult:
    """Run the whole scenario and write the evidence pack to `settings.evidence_dir`."""
```

**Function `run_demo`.** Run the whole scenario and write the evidence pack to `settings.evidence_dir`.

It takes: `settings` (a `Settings`); `root` (a `Path`), default `Path()`.

It gives back a `DemoResult`.

`src/pci_scope/interfaces/demo.py` lines 63 to 77:

```python
    state = settings.state_dir
    shutil.rmtree(state, ignore_errors=True)
    shutil.rmtree(settings.evidence_dir, ignore_errors=True)
    (state / "merchant").mkdir(parents=True)
    (state / "backups").mkdir()
    app_log = state / "merchant" / "app.log"
    handler = logging.FileHandler(app_log, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    merchant_logger = logging.getLogger("merchant")
    merchant_logger.setLevel(logging.INFO)
    merchant_logger.handlers[:] = [handler]
    merchant_logger.propagate = False

    orders = SqliteOrders(settings.database_path)
    orders.initialize((root / "sql" / "001_schema.sql").read_text(encoding="utf-8"))
```

> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**`run_demo`, part 1 of 3.**

Step by step:

- Stores `settings.state_dir` in `state`.
- Calls `shutil.rmtree(state, ignore_errors=True)`.
- Calls `shutil.rmtree(settings.evidence_dir, ignore_errors=True)`.
- Calls `(state / 'merchant').mkdir(parents=True)`.
- Calls `(state / 'backups').mkdir()`.
- Stores `state / 'merchant' / 'app.log'` in `app_log`.
- Stores the result of calling `logging.FileHandler(app_log, encoding='utf-8')` in `handler`.
- Calls `handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))`.
- Stores the result of calling `logging.getLogger('merchant')` in `merchant_logger`.
- Calls `merchant_logger.setLevel(logging.INFO)`.
- Stores the list `[handler]` in `merchant_logger.handlers[:]`.
- Stores `False` in `merchant_logger.propagate`.
- Stores the result of calling `SqliteOrders(settings.database_path)` in `orders`.
- Calls `orders.initialize((root / 'sql' / '001_schema.sql').read_text(encoding='utf-8'))`.

`src/pci_scope/interfaces/demo.py` lines 78 to 115:

```python
    provider_state = ProviderState(
        settings.secret_key, settings.publishable_key, settings.webhook_secret, f"{settings.merchant_base_url}/webhook"
    )
    checkout = CheckoutService(
        HttpProvider(settings.provider_base_url, settings.secret_key), orders, settings.webhook_secret
    )
    provider_app = create_provider_app(provider_state)
    merchant_app = create_merchant_app(checkout, settings.provider_public_url, settings.publishable_key)
    naive_app = create_naive_app(settings.naive_log_path)

    try:
        with (
            LocalServer(provider_app, _port(settings.provider_base_url)),
            LocalServer(merchant_app, _port(settings.merchant_base_url)),
            LocalServer(naive_app, _port(settings.naive_base_url)),
        ):
            pay_on_naive_checkout(Browser(), settings.naive_base_url)
            browser = Browser()
            run = pay_with_hosted_fields(
                browser, settings.merchant_base_url, settings.provider_base_url, settings.publishable_key
            )
            again = json.loads(
                Browser()
                .request(
                    "POST", f"{settings.merchant_base_url}/charge-again", payload={"payment_intent": run.intent_id}
                )
                .body
            )
            Browser().request(
                "POST", f"{settings.merchant_base_url}/refund", payload={"payment_intent": again["payment_intent"]}
            )
            probe = Browser()
            routes = [
                ("POST", "/pay", probe.request("POST", f"{settings.merchant_base_url}/pay").status),
                ("GET", "/pay", probe.request("GET", f"{settings.merchant_base_url}/pay").status),
            ]
    finally:
        handler.close()
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**`run_demo`, part 2 of 3.**

Step by step:

- Stores the result of calling `ProviderState(settings.secret_key, settings.publishable_key, settings.webhook_secret, f'{…` in `provider_state`.
- Stores the result of calling `CheckoutService(HttpProvider(settings.provider_base_url, settings.secret_key), orders, se…` in `checkout`.
- Stores the result of calling `create_provider_app(provider_state)` in `provider_app`.
- Stores the result of calling `create_merchant_app(checkout, settings.provider_public_url, settings.publishable_key)` in `merchant_app`.
- Stores the result of calling `create_naive_app(settings.naive_log_path)` in `naive_app`.
- Tries:
  - Inside a `with` block that opens `LocalServer(provider_app, _port(settings.provider_base_url))`; `LocalServer(merchant_app, _port(settings.merchant_base_url))`; `LocalServer(naive_app, _port(settings.naive_base_url))`:
    - Calls `pay_on_naive_checkout(Browser(), settings.naive_base_url)`.
    - Stores the result of calling `Browser()` in `browser`.
    - Stores the result of calling `pay_with_hosted_fields(browser, settings.merchant_base_url, settings.provider_base_url, s…` in `run`.
    - Stores the result of calling `json.loads(Browser().request('POST', f'{settings.merchant_base_url}/charge-again', payloa…` in `again`.
    - Calls `Browser().request('POST', f'{settings.merchant_base_url}/refund', payload={'payment_intent': again['payment_i…`.
    - Stores the result of calling `Browser()` in `probe`.
    - Stores the list `[('POST', '/pay', probe.request('POST', f'{settings.merchant_base_url…` in `routes`.
- Always, at the end:
  - Calls `handler.close()`.

`src/pci_scope/interfaces/demo.py` lines 117 to 129:

```python
    (state / "backups" / "merchant-backup.sql").write_text(orders.dump(), encoding="utf-8")
    before = run_scan("scanning the naive checkout after one test payment:", NaiveArtifacts(settings.naive_log_path))
    artifacts = MerchantArtifacts(state, orders.dump, settings.database_path, skip=("naive",))
    after = run_scan("scanning the merchant's side after the same payment, a repeat charge and a refund:", artifacts)
    statuses: dict[str, str] = {}
    for intent_id in (run.intent_id, again["payment_intent"]):
        found = orders.find(intent_id)
        if found is not None:
            statuses[intent_id] = found.status
    _write_pack(settings, run, before, after, routes, orders, root)
    return DemoResult(
        before, after, run, statuses, tuple(sorted(path.name for path in settings.evidence_dir.iterdir()))
    )
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**`run_demo`, part 3 of 3.**

Step by step:

- Calls `(state / 'backups' / 'merchant-backup.sql').write_text(orders.dump(), encoding='utf-8')`.
- Stores the result of calling `run_scan('scanning the naive checkout after one test payment:', NaiveArtifacts(settings.n…` in `before`.
- Stores the result of calling `MerchantArtifacts(state, orders.dump, settings.database_path, skip=('naive',))` in `artifacts`.
- Stores the result of calling `run_scan("scanning the merchant's side after the same payment, a repeat charge and a refu…` in `after`.
- Declares `statuses` as a `dict[str, str]` and stores the dictionary `{}` in it.
- For each `intent_id` in the tuple `(run.intent_id, again['payment_intent'])`:
  - Stores the result of calling `orders.find(intent_id)` in `found`.
  - If `found` is not the same object as `None`:
    - Stores `found.status` in `statuses[intent_id]`.
- Calls `_write_pack(settings, run, before, after, routes, orders, root)`.
- Gives back the result of calling `DemoResult(before, after, run, statuses, tuple(sorted((path.name for path in settings.evi…`.

`src/pci_scope/interfaces/demo.py` lines 132 to 136:

```python
def _grep(label: str, pattern: str, ignore_case: bool, paths: list[Path]) -> str:
    command = ["grep", "-rnaE", *(["-i"] if ignore_case else []), pattern, *map(str, paths)]
    done = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
    shown = f"$ grep -rnaE{' -i' if ignore_case else ''} '{pattern}' {' '.join(path.name for path in paths)}"
    return f"{shown}\n{'' if done.returncode == 1 else done.stdout}exit={done.returncode}  ({label})\n"
```

> **In plain words.** `*items` **unpacks** a sequence into separate values; `**options` does the same for a dictionary's keys and values.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `_grep`.**

It takes: `label` (a `str`); `pattern` (a `str`); `ignore_case` (a `bool`); `paths` (a `list[Path]`).

It gives back a `str`.

Step by step:

- Stores the list `['grep', '-rnaE', *(['-i'] if ignore_case else []), pattern, *map(str…` in `command`.
- Stores the result of calling `subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)` in `done`.
- Stores a text built with values filled in (`f"$ grep -rnaE{(' -i' if ignore_case else '')} '{pattern}' {' '.join(…`) in `shown`.
- Gives back a text built with values filled in (`f"{shown}\n{('' if done.returncode == 1 else done.stdout)}exit={done.…`).

`src/pci_scope/interfaces/demo.py` lines 139 to 147:

```python
def _write_pack(
    settings: Settings,
    run: PaymentRun,
    before: ScanOutcome,
    after: ScanOutcome,
    routes: list[tuple[str, str, int]],
    orders: SqliteOrders,
    root: Path,
) -> None:
```

**Function `_write_pack`.**

It takes: `settings` (a `Settings`); `run` (a `PaymentRun`); `before` (a `ScanOutcome`); `after` (a `ScanOutcome`); `routes` (a `list[tuple[str, str, int]]`); `orders` (a `SqliteOrders`); `root` (a `Path`).

It gives back a `None`.

`src/pci_scope/interfaces/demo.py` lines 148 to 167:

```python
    store = FileEvidenceStore(settings.evidence_dir)
    now = datetime.now(UTC)
    inventories = scope_documents(
        load_inventory(root / "scope" / "before.toml"), load_inventory(root / "scope" / "after.toml")
    )
    for name, text in inventories.items():
        store.write(name, text, "P3", now)
    store.write("proof-before.txt", before.text, "P4", now)
    merchant_paths = [settings.database_path, settings.state_dir / "merchant", settings.state_dir / "backups"]
    greps = _grep("no card number found", GREP_PAN, False, merchant_paths) + _grep(
        "no card field found", GREP_FIELDS, True, merchant_paths
    )
    store.write(
        "proof-after.txt",
        after.text
        + "\nthe lesson's own checks, on the same places (grep exits 1 when nothing is found; -a reads SQLite too):\n"
        + greps,
        "P1",
        now,
    )
```

**`_write_pack`, part 1 of 4.**

Step by step:

- Stores the result of calling `FileEvidenceStore(settings.evidence_dir)` in `store`.
- Stores the result of calling `datetime.now(UTC)` in `now`.
- Stores the result of calling `scope_documents(load_inventory(root / 'scope' / 'before.toml'), load_inventory(root / 'sc…` in `inventories`.
- For each `(name, text)` in the result of calling `inventories.items()`:
  - Calls `store.write(name, text, 'P3', now)`.
- Calls `store.write('proof-before.txt', before.text, 'P4', now)`.
- Stores the list `[settings.database_path, settings.state_dir / 'merchant', settings.st…` in `merchant_paths`.
- Stores `_grep('no card number found', GREP_PAN, False, merchant_paths) + _grep('no card…` in `greps`.
- Calls `store.write('proof-after.txt', after.text + "\nthe lesson's own checks, on the same places (grep exits 1 when…`.

`src/pci_scope/interfaces/demo.py` lines 168 to 181:

```python
    redact = frozenset({settings.provider_base_url})
    store.write("payment.har", to_har(run.exchanges, redact), "P1", now)
    store.write(
        "payment-summary.txt",
        summarize(run.exchanges, settings.merchant_base_url, settings.provider_base_url),
        "P1",
        now,
    )
    store.write("route-check.txt", render_routes(routes), "P2", now)
    digit_columns = [
        name
        for name, kind in orders.columns()
        if kind.upper() in ("REAL",) or name in ("card_number", "cvv", "cvc", "pan")
    ]
```

> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**`_write_pack`, part 2 of 4.**

Step by step:

- Stores the result of calling `frozenset({settings.provider_base_url})` in `redact`.
- Calls `store.write('payment.har', to_har(run.exchanges, redact), 'P1', now)`.
- Calls `store.write('payment-summary.txt', summarize(run.exchanges, settings.merchant_base_url, settings.provider_bas…`.
- Calls `store.write('route-check.txt', render_routes(routes), 'P2', now)`.
- Stores a new list made by a loop (`[name for name, kind in orders.columns() if kind.upper() in ('REAL',)…`) in `digit_columns`.

`src/pci_scope/interfaces/demo.py` lines 182 to 195:

```python
    store.write("token-storage.txt", render_token_storage(orders.columns(), orders.rows(), digit_columns), "P5", now)
    store.write(
        "checkout-page-controls.txt",
        render_page_controls(
            f"{settings.merchant_base_url}/",
            200,
            run.page_headers,
            run.scripts,
            settings.provider_base_url,
            run.page_card_fields,
        ),
        "P6",
        now,
    )
```

**`_write_pack`, part 3 of 4.**

Step by step:

- Calls `store.write('token-storage.txt', render_token_storage(orders.columns(), orders.rows(), digit_columns), 'P5', …`.
- Calls `store.write('checkout-page-controls.txt', render_page_controls(f'{settings.merchant_base_url}/', 200, run.pag…`.

`src/pci_scope/interfaces/demo.py` lines 196 to 204:

```python
    for name, requirement in (("responsibilities.md", "P6"), ("provider-attestation.md", "P7")):
        store.write(
            name,
            (root / "docs" / name).read_text(encoding="utf-8"),
            requirement,
            now,
        )
    requirements, gaps = load_requirements(root / "controls" / "requirements.toml")
    store.write("INDEX.md", render_index(requirements, store.manifest(), gaps, now), "-", now)
```

**`_write_pack`, part 4 of 4.**

Step by step:

- For each `(name, requirement)` in the tuple `(('responsibilities.md', 'P6'), ('provider-attestation.md', 'P7'))`:
  - Calls `store.write(name, (root / 'docs' / name).read_text(encoding='utf-8'), requirement, now)`.
- Unpacks the result of calling `load_requirements(root / 'controls' / 'requirements.toml')` into `(requirements, gaps)`.
- Calls `store.write('INDEX.md', render_index(requirements, store.manifest(), gaps, now), '-', now)`.

### `src/pci_scope/interfaces/factories.py`

`src/pci_scope/interfaces/factories.py` lines 1 to 17:

```python
"""Application factories for gunicorn: `gunicorn "pci_scope.interfaces.factories:merchant()"`."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from pci_scope.application.checkout import CheckoutService
from pci_scope.infrastructure.logging_setup import configure_logging
from pci_scope.infrastructure.provider_http import HttpProvider
from pci_scope.infrastructure.settings import load_settings
from pci_scope.infrastructure.sqlite_orders import SqliteOrders
from pci_scope.interfaces.merchant_app import create_merchant_app
from pci_scope.interfaces.naive_app import create_naive_app
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Application factories for gunicorn: `gunicorn "pci_scope.interfaces.factories:merchant()"`.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `os`.
- From `pathlib` it takes `Path`.
- From `flask` it takes `Flask`.
- From `pci_scope.application.checkout` it takes `CheckoutService`.
- From `pci_scope.infrastructure.logging_setup` it takes `configure_logging`.
- From `pci_scope.infrastructure.provider_http` it takes `HttpProvider`.
- From `pci_scope.infrastructure.settings` it takes `load_settings`.
- From `pci_scope.infrastructure.sqlite_orders` it takes `SqliteOrders`.
- From `pci_scope.interfaces.merchant_app` it takes `create_merchant_app`.
- From `pci_scope.interfaces.naive_app` it takes `create_naive_app`.
- From `pci_scope.interfaces.provider_app` it takes `ProviderState, create_provider_app`.

`src/pci_scope/interfaces/factories.py` lines 19 to 19:

```python
SCHEMA = Path("sql/001_schema.sql")
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `Path('sql/001_schema.sql')` in `SCHEMA`.

`src/pci_scope/interfaces/factories.py` lines 22 to 29:

```python
def provider() -> Flask:
    """The local payment provider. State is in memory, so run it with one worker."""
    settings = load_settings(os.environ)
    configure_logging(settings.log_level)
    state = ProviderState(
        settings.secret_key, settings.publishable_key, settings.webhook_secret, f"{settings.merchant_base_url}/webhook"
    )
    return create_provider_app(state)
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `provider`.** The local payment provider. State is in memory, so run it with one worker.

It gives back a `Flask`.

Step by step:

- Stores the result of calling `load_settings(os.environ)` in `settings`.
- Calls `configure_logging(settings.log_level)`.
- Stores the result of calling `ProviderState(settings.secret_key, settings.publishable_key, settings.webhook_secret, f'{…` in `state`.
- Gives back the result of calling `create_provider_app(state)`.

`src/pci_scope/interfaces/factories.py` lines 32 to 41:

```python
def merchant() -> Flask:
    """The redesigned merchant."""
    settings = load_settings(os.environ)
    configure_logging(settings.log_level)
    orders = SqliteOrders(settings.database_path)
    orders.initialize(SCHEMA.read_text(encoding="utf-8"))
    checkout = CheckoutService(
        HttpProvider(settings.provider_base_url, settings.secret_key), orders, settings.webhook_secret
    )
    return create_merchant_app(checkout, settings.provider_public_url, settings.publishable_key)
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Function `merchant`.** The redesigned merchant.

It gives back a `Flask`.

Step by step:

- Stores the result of calling `load_settings(os.environ)` in `settings`.
- Calls `configure_logging(settings.log_level)`.
- Stores the result of calling `SqliteOrders(settings.database_path)` in `orders`.
- Calls `orders.initialize(SCHEMA.read_text(encoding='utf-8'))`.
- Stores the result of calling `CheckoutService(HttpProvider(settings.provider_base_url, settings.secret_key), orders, se…` in `checkout`.
- Gives back the result of calling `create_merchant_app(checkout, settings.provider_public_url, settings.publishable_key)`.

`src/pci_scope/interfaces/factories.py` lines 44 to 47:

```python
def naive() -> Flask:
    """The naive checkout, only to be measured."""
    settings = load_settings(os.environ)
    return create_naive_app(settings.naive_log_path)
```

**Function `naive`.** The naive checkout, only to be measured.

It gives back a `Flask`.

Step by step:

- Stores the result of calling `load_settings(os.environ)` in `settings`.
- Gives back the result of calling `create_naive_app(settings.naive_log_path)`.

### `src/pci_scope/interfaces/merchant_app.py`

`src/pci_scope/interfaces/merchant_app.py` lines 1 to 14:

```python
"""The merchant's web app after the redesign: it serves the page, creates the payment, asks the provider the result.

There is no route that accepts a card number. A request body is never logged.
"""

from __future__ import annotations

import logging
import time

from flask import Flask, Response, jsonify, request

from pci_scope.application.checkout import CheckoutService
from pci_scope.domain.payment import Order, PaymentError
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The merchant's web app after the redesign: it serves the page, creates the payment, asks the provider the result. There is no route that accepts a card number. A request body is never logged.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `logging`.
- It imports module `time`.
- From `flask` it takes `Flask, Response, jsonify, request`.
- From `pci_scope.application.checkout` it takes `CheckoutService`.
- From `pci_scope.domain.payment` it takes `Order, PaymentError`.

`src/pci_scope/interfaces/merchant_app.py` lines 16 to 28:

```python
logger = logging.getLogger("merchant")

PAGE = """\
<!doctype html>
<meta charset="utf-8">
<title>Checkout</title>
<h1>Pay 19.00 EUR</h1>
<div id="card"></div>
<button id="pay" type="button">Pay 19.00</button>
<p id="message" role="status"></p>
<script src="__PROVIDER__/v1/elements.js"></script>
<script src="/static/checkout.js" data-key="__KEY__"></script>
"""
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `logging.getLogger('merchant')` in `logger`.
- Stores the text `'<!doctype html>\n<meta charset="utf-8">\n<title>Checkout</…` in `PAGE`.

`src/pci_scope/interfaces/merchant_app.py` lines 30 to 41:

```python
CHECKOUT_JS = """\
(async function () {
  var key = document.currentScript.dataset.key;
  var provider = Provider(key);
  var started = await (await fetch("/create-payment", { method: "POST" })).json();
  var elements = provider.elements({ clientSecret: started.clientSecret });
  elements.create("payment").mount("#card");
  document.querySelector("#pay").onclick = function () {
    provider.confirmPayment({ elements: elements, confirmParams: { return_url: location.origin + "/done" } });
  };
})();
"""
```

These module-level lines:

- Stores the text `'(async function () {\n var key = document.currentScript.da…` in `CHECKOUT_JS`.

`src/pci_scope/interfaces/merchant_app.py` lines 44 to 51:

```python
def _order_json(order: Order) -> dict[str, object]:
    return {
        "id": order.id,
        "payment_intent": order.payment_intent_id,
        "status": order.status,
        "amount": order.amount_cents,
        "currency": order.currency,
    }
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Function `_order_json`.**

It takes: `order` (a `Order`).

It gives back a `dict[str, object]`.

Step by step:

- Gives back the dictionary `{'id': order.id, 'payment_intent': order.payment_intent_id, 'status':…`.

`src/pci_scope/interfaces/merchant_app.py` lines 54 to 55:

```python
def create_merchant_app(checkout: CheckoutService, provider_base_url: str, publishable_key: str) -> Flask:
    """The merchant's routes. The page's content security policy names the provider and nothing else."""
```

**Function `create_merchant_app`.** The merchant's routes. The page's content security policy names the provider and nothing else.

It takes: `checkout` (a `CheckoutService`); `provider_base_url` (a `str`); `publishable_key` (a `str`).

It gives back a `Flask`.

`src/pci_scope/interfaces/merchant_app.py` lines 56 to 73:

```python
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    policy = (
        f"default-src 'self'; script-src 'self' {provider_base_url}; frame-src {provider_base_url}; "
        f"connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    )

    @app.after_request
    def secure(response: Response) -> Response:
        response.headers["Content-Security-Policy"] = policy
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/healthz")
    def healthz() -> Response:
        return jsonify(status="ok")
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**`create_merchant_app`, part 1 of 5.**

Step by step:

- Stores the result of calling `Flask(__name__)` in `app`.
- Stores `16 * 1024` in `app.config['MAX_CONTENT_LENGTH']`.
- Stores a text built with values filled in (`f"default-src 'self'; script-src 'self' {provider_base_url}; frame-sr…`) in `policy`.
- Defines a helper function `secure(response)`.
  - Stores `policy` in `response.headers['Content-Security-Policy']`.
  - Stores the text `'nosniff'` in `response.headers['X-Content-Type-Options']`.
  - Stores the text `'no-referrer'` in `response.headers['Referrer-Policy']`.
  - Stores the text `'no-store'` in `response.headers['Cache-Control']`.
  - Gives back `response`.
- Defines a helper function `healthz()`.
  - Gives back the result of calling `jsonify(status='ok')`.

`src/pci_scope/interfaces/merchant_app.py` lines 75 to 95:

```python
    @app.get("/")
    def page() -> Response:
        return Response(
            PAGE.replace("__PROVIDER__", provider_base_url).replace("__KEY__", publishable_key), mimetype="text/html"
        )

    @app.get("/static/checkout.js")
    def script() -> Response:
        return Response(CHECKOUT_JS, mimetype="text/javascript")

    @app.post("/create-payment")
    def create_payment() -> Response:
        started = checkout.start()
        logger.info("created payment %s amount=1900 eur", started.intent_id)
        return jsonify(clientSecret=started.client_secret, id=started.intent_id)

    @app.get("/done")
    def done() -> tuple[str, int]:
        order = checkout.complete(request.args.get("payment_intent", ""))
        logger.info("payment %s status=%s", order.payment_intent_id, order.status)
        return (f"payment {order.payment_intent_id}: {order.status}", 200 if order.status == "succeeded" else 402)
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**`create_merchant_app`, part 2 of 5.**

Step by step:

- Defines a helper function `page()`.
  - Gives back the result of calling `Response(PAGE.replace('__PROVIDER__', provider_base_url).replace('__KEY__', publishable_k…`.
- Defines a helper function `script()`.
  - Gives back the result of calling `Response(CHECKOUT_JS, mimetype='text/javascript')`.
- Defines a helper function `create_payment()`.
  - Stores the result of calling `checkout.start()` in `started`.
  - Calls `logger.info('created payment %s amount=1900 eur', started.intent_id)`.
  - Gives back the result of calling `jsonify(clientSecret=started.client_secret, id=started.intent_id)`.
- Defines a helper function `done()`.
  - Stores the result of calling `checkout.complete(request.args.get('payment_intent', ''))` in `order`.
  - Calls `logger.info('payment %s status=%s', order.payment_intent_id, order.status)`.
  - Gives back the tuple `(f'payment {order.payment_intent_id}: {order.status}', 200 if order.s…`.

`src/pci_scope/interfaces/merchant_app.py` lines 97 to 114:

```python
    @app.post("/charge-again")
    def charge_again() -> Response:
        order = checkout.charge_again((request.get_json(silent=True) or {}).get("payment_intent", ""))
        logger.info("repeat charge %s status=%s", order.payment_intent_id, order.status)
        return jsonify(_order_json(order))

    @app.post("/refund")
    def refund() -> Response:
        intent = (request.get_json(silent=True) or {}).get("payment_intent", "")
        refund_id = checkout.refund(intent)
        logger.info("refunded %s as %s", intent, refund_id)
        return jsonify(refund=refund_id, payment_intent=intent)

    @app.post("/webhook")
    def webhook() -> Response:
        outcome = checkout.handle_event(request.get_data(), request.headers.get("Provider-Signature"), int(time.time()))
        logger.info("webhook %s", outcome)
        return jsonify(outcome=outcome)
```

**`create_merchant_app`, part 3 of 5.**

Step by step:

- Defines a helper function `charge_again()`.
  - Stores the result of calling `checkout.charge_again((request.get_json(silent=True) or {}).get('payment_intent', ''))` in `order`.
  - Calls `logger.info('repeat charge %s status=%s', order.payment_intent_id, order.status)`.
  - Gives back the result of calling `jsonify(_order_json(order))`.
- Defines a helper function `refund()`.
  - Stores the result of calling `(request.get_json(silent=True) or {}).get('payment_intent', '')` in `intent`.
  - Stores the result of calling `checkout.refund(intent)` in `refund_id`.
  - Calls `logger.info('refunded %s as %s', intent, refund_id)`.
  - Gives back the result of calling `jsonify(refund=refund_id, payment_intent=intent)`.
- Defines a helper function `webhook()`.
  - Stores the result of calling `checkout.handle_event(request.get_data(), request.headers.get('Provider-Signature'), int(…` in `outcome`.
  - Calls `logger.info('webhook %s', outcome)`.
  - Gives back the result of calling `jsonify(outcome=outcome)`.

`src/pci_scope/interfaces/merchant_app.py` lines 116 to 132:

```python
    @app.errorhandler(PaymentError)
    def payment_failed(problem: PaymentError) -> tuple[Response, int]:
        logger.warning("payment error: %s", problem)
        return jsonify(error=str(problem)), 402

    @app.errorhandler(404)
    def not_found(_: Exception) -> tuple[Response, int]:
        return jsonify(error="not found"), 404

    @app.errorhandler(413)
    def too_large(_: Exception) -> tuple[Response, int]:
        return jsonify(error="request too large"), 413

    @app.errorhandler(Exception)
    def unexpected(problem: Exception) -> tuple[Response, int]:
        logger.error("unhandled %s", type(problem).__name__)
        return jsonify(error="internal error"), 500
```

**`create_merchant_app`, part 4 of 5.**

Step by step:

- Defines a helper function `payment_failed(problem)`.
  - Calls `logger.warning('payment error: %s', problem)`.
  - Gives back the tuple `(jsonify(error=str(problem)), 402)`.
- Defines a helper function `not_found(_)`.
  - Gives back the tuple `(jsonify(error='not found'), 404)`.
- Defines a helper function `too_large(_)`.
  - Gives back the tuple `(jsonify(error='request too large'), 413)`.
- Defines a helper function `unexpected(problem)`.
  - Calls `logger.error('unhandled %s', type(problem).__name__)`.
  - Gives back the tuple `(jsonify(error='internal error'), 500)`.

`src/pci_scope/interfaces/merchant_app.py` lines 134 to 134:

```python
    return app
```

**`create_merchant_app`, part 5 of 5.**

Step by step:

- Gives back `app`.

### `src/pci_scope/interfaces/naive_app.py`

`src/pci_scope/interfaces/naive_app.py` lines 1 to 11:

```python
"""The "before": the lesson's naive checkout. It posts card details to its own server and logs the whole form.

This app exists to be scanned and measured. Do not run it with anything but the provider's published test card.
"""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, request
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The "before": the lesson's naive checkout. It posts card details to its own server and logs the whole form. This app exists to be scanned and measured. Do not run it with anything but the provider's published test card.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `logging`.
- From `pathlib` it takes `Path`.
- From `flask` it takes `Flask, request`.

`src/pci_scope/interfaces/naive_app.py` lines 13 to 15:

```python
FORM = """<form method="post" action="/pay">
  Card <input name="card_number"> Expiry <input name="expiry"> CVV <input name="cvv">
  <button>Pay 19.00</button></form>"""
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'<form method="post" action="/pay">\n Card <input name="car…` in `FORM`.

`src/pci_scope/interfaces/naive_app.py` lines 18 to 38:

```python
def create_naive_app(log_path: Path) -> Flask:
    """The naive app, logging requests to `log_path`."""
    app = Flask(__name__)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger = logging.getLogger(f"naive.{log_path}")
    logger.setLevel(logging.INFO)
    logger.handlers[:] = [handler]
    logger.propagate = False

    @app.get("/")
    def checkout() -> str:
        return FORM

    @app.post("/pay")
    def pay() -> str:
        logger.info("payment request: %s", dict(request.form))  # the mistake: card data reaches the log
        return "paid (simulated)"

    return app
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `create_naive_app`.** The naive app, logging requests to `log_path`.

It takes: `log_path` (a `Path`).

It gives back a `Flask`.

Step by step:

- Stores the result of calling `Flask(__name__)` in `app`.
- Calls `log_path.parent.mkdir(parents=True, exist_ok=True)`.
- Stores the result of calling `logging.FileHandler(log_path, encoding='utf-8')` in `handler`.
- Calls `handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))`.
- Stores the result of calling `logging.getLogger(f'naive.{log_path}')` in `logger`.
- Calls `logger.setLevel(logging.INFO)`.
- Stores the list `[handler]` in `logger.handlers[:]`.
- Stores `False` in `logger.propagate`.
- Defines a helper function `checkout()`.
  - Gives back `FORM`.
- Defines a helper function `pay()`.
  - Calls `logger.info('payment request: %s', dict(request.form))`.
  - Gives back the text `'paid (simulated)'`.
- Gives back `app`.

### `src/pci_scope/interfaces/provider_app.py`

`src/pci_scope/interfaces/provider_app.py` lines 1 to 23:

```python
"""A local stand-in for a payment provider's test mode: the same shape of API as a real one, with hosted fields.

The card form is served from this origin, in an iframe. The merchant's page loads only a script and the iframe from
here; the card number goes from the customer's browser to this app and never to the merchant. State is in memory.
"""

from __future__ import annotations

import contextlib
import json
import secrets
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from flask import Flask, Response, jsonify, request

from pci_scope.domain.card import DECLINED_TEST_CARD, luhn_valid
from pci_scope.domain.webhook import sign
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** A local stand-in for a payment provider's test mode: the same shape of API as a real one, with hosted fields. The card form is served from this origin, in an iframe. The merchant's page loads only a script and the iframe from here; the card number goes from the customer's browser to this app and never to the merchant. State is in memory.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `contextlib`.
- It imports module `json`.
- It imports module `secrets`.
- It imports module `threading`.
- It imports module `time`.
- It imports module `urllib.error`.
- It imports module `urllib.request`.
- From `collections.abc` it takes `Callable`.
- From `dataclasses` it takes `dataclass, field`.
- From `typing` it takes `Any`.
- From `flask` it takes `Flask, Response, jsonify, request`.
- From `pci_scope.domain.card` it takes `DECLINED_TEST_CARD, luhn_valid`.
- From `pci_scope.domain.webhook` it takes `sign`.

`src/pci_scope/interfaces/provider_app.py` lines 25 to 25:

```python
Deliver = Callable[[str, bytes, str], None]
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

These module-level lines:

- Stores `Callable[[str, bytes, str], None]` in `Deliver`.

`src/pci_scope/interfaces/provider_app.py` lines 28 to 29:

```python
def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(12)}"
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `_id`.**

It takes: `prefix` (a `str`).

It gives back a `str`.

Step by step:

- Gives back a text built with values filled in (`f'{prefix}_{secrets.token_hex(12)}'`).

`src/pci_scope/interfaces/provider_app.py` lines 32 to 38:

```python
def deliver_over_http(url: str, body: bytes, signature: str) -> None:
    """POST a webhook with a timeout; a failure is logged by the caller, never raised into the payment."""
    http = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/json", "Provider-Signature": signature}
    )
    with urllib.request.urlopen(http, timeout=5):
        pass
```

> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Function `deliver_over_http`.** POST a webhook with a timeout; a failure is logged by the caller, never raised into the payment.

It takes: `url` (a `str`); `body` (a `bytes`); `signature` (a `str`).

It gives back a `None`.

Step by step:

- Stores the result of calling `urllib.request.Request(url, data=body, method='POST', headers={'Content-Type': 'applicati…` in `http`.
- Inside a `with` block that opens `urllib.request.urlopen(http, timeout=5)`:
  - Does nothing (`pass`).

`src/pci_scope/interfaces/provider_app.py` lines 41 to 55:

```python
@dataclass
class ProviderState:
    """Everything the provider holds. A real one holds the card; this one keeps only brand and last four digits."""

    secret_key: str
    publishable_key: str
    webhook_secret: str
    webhook_url: str
    deliver: Deliver = deliver_over_http
    intents: dict[str, dict[str, Any]] = field(default_factory=dict)
    methods: dict[str, dict[str, Any]] = field(default_factory=dict)
    customers: set[str] = field(default_factory=set)
    refunds: dict[str, str] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `ProviderState`**. Everything the provider holds. A real one holds the card; this one keeps only brand and last four digits. Decorators: `@dataclass`.

Its parts:

- Field `secret_key`: a `str`.
- Field `publishable_key`: a `str`.
- Field `webhook_secret`: a `str`.
- Field `webhook_url`: a `str`.
- Field `deliver`: a `Deliver`, default `deliver_over_http`.
- Field `intents`: a `dict[str, dict[str, Any]]`, default `field(default_factory=dict)`.
- Field `methods`: a `dict[str, dict[str, Any]]`, default `field(default_factory=dict)`.
- Field `customers`: a `set[str]`, default `field(default_factory=set)`.
- Field `refunds`: a `dict[str, str]`, default `field(default_factory=dict)`.
- Field `events`: a `list[dict[str, Any]]`, default `field(default_factory=list)`.
- Field `lock`: a `threading.Lock`, default `field(default_factory=threading.Lock)`.

`src/pci_scope/interfaces/provider_app.py` lines 58 to 59:

```python
def _public(intent: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in intent.items() if key not in ("confirmed_with",)}
```

> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `_public`.**

It takes: `intent` (a `dict[str, Any]`).

It gives back a `dict[str, Any]`.

Step by step:

- Gives back a new dictionary made by a loop (`{key: value for key, value in intent.items() if key not in ('confirme…`).

`src/pci_scope/interfaces/provider_app.py` lines 62 to 63:

```python
def create_provider_app(state: ProviderState) -> Flask:
    """The provider's API, its script and its hosted card form."""
```

**Function `create_provider_app`.** The provider's API, its script and its hosted card form.

It takes: `state` (a `ProviderState`).

It gives back a `Flask`.

`src/pci_scope/interfaces/provider_app.py` lines 64 to 81:

```python
    app = Flask(__name__)

    def error(status: int, kind: str, message: str) -> tuple[Response, int]:
        return jsonify(error={"type": kind, "message": message}), status

    def secret_ok() -> bool:
        return request.headers.get("Authorization", "") == f"Bearer {state.secret_key}"

    def publishable_ok() -> bool:
        return (request.headers.get("X-Publishable-Key") or request.form.get("key", "")) == state.publishable_key

    def emit(kind: str, intent: dict[str, Any]) -> None:
        event = {"id": _id("evt"), "type": kind, "data": {"object": _public(intent)}}
        state.events.append(event)
        body = json.dumps(event).encode()
        # If the merchant is down the event is lost; a real provider retries for days.
        with contextlib.suppress(urllib.error.URLError, OSError, TimeoutError):
            state.deliver(state.webhook_url, body, sign(state.webhook_secret, body, int(time.time())))
```

**`create_provider_app`, part 1 of 6.**

Step by step:

- Stores the result of calling `Flask(__name__)` in `app`.
- Defines a helper function `error(status, kind, message)`.
  - Gives back the tuple `(jsonify(error={'type': kind, 'message': message}), status)`.
- Defines a helper function `secret_ok()`.
  - Gives back whether `request.headers.get('Authorization', '')` equals `f'Bearer {state.secret_key}'`.
- Defines a helper function `publishable_ok()`.
  - Gives back whether `request.headers.get('X-Publishable-Key') or reque…` equals `state.publishable_key`.
- Defines a helper function `emit(kind, intent)`.
  - Stores the dictionary `{'id': _id('evt'), 'type': kind, 'data': {'object': _public(intent)}}` in `event`.
  - Calls `state.events.append(event)`.
  - Stores the result of calling `json.dumps(event).encode()` in `body`.
  - Inside a `with` block that opens `contextlib.suppress(urllib.error.URLError, OSError, TimeoutError)`:
    - Calls `state.deliver(state.webhook_url, body, sign(state.webhook_secret, body, int(time.time())))`.

`src/pci_scope/interfaces/provider_app.py` lines 83 to 101:

```python
    @app.get("/healthz")
    def healthz() -> Response:
        return jsonify(status="ok")

    @app.get("/v1/elements.js")
    def elements_js() -> Response:
        return Response(ELEMENTS_JS, mimetype="text/javascript")

    @app.get("/frame")
    def frame() -> Response:
        origin = request.args.get("origin", "")
        page = FRAME_HTML.replace("__KEY__", state.publishable_key).replace(
            "__SECRET__", request.args.get("client_secret", "").replace('"', "")
        )
        response = Response(page, mimetype="text/html")
        response.headers["Content-Security-Policy"] = (
            f"frame-ancestors {origin or 'none'}; default-src 'self'; script-src 'self' 'unsafe-inline'"
        )
        return response
```

**`create_provider_app`, part 2 of 6.**

Step by step:

- Defines a helper function `healthz()`.
  - Gives back the result of calling `jsonify(status='ok')`.
- Defines a helper function `elements_js()`.
  - Gives back the result of calling `Response(ELEMENTS_JS, mimetype='text/javascript')`.
- Defines a helper function `frame()`.
  - Stores the result of calling `request.args.get('origin', '')` in `origin`.
  - Stores the result of calling `FRAME_HTML.replace('__KEY__', state.publishable_key).replace('__SECRET__', request.args.g…` in `page`.
  - Stores the result of calling `Response(page, mimetype='text/html')` in `response`.
  - Stores a text built with values filled in (`f"frame-ancestors {origin or 'none'}; default-src 'self'; script-src …`) in `response.headers['Content-Security-Policy']`.
  - Gives back `response`.

`src/pci_scope/interfaces/provider_app.py` lines 103 to 120:

```python
    @app.post("/v1/customers")
    def create_customer() -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        customer = _id("cus")
        state.customers.add(customer)
        return jsonify(id=customer)

    @app.post("/v1/payment_methods")
    def create_method() -> tuple[Response, int] | Response:
        if not publishable_ok():
            return error(401, "authentication_error", "Invalid publishable key")
        number = request.form.get("card[number]", "").replace(" ", "")
        if not luhn_valid(number) or not request.form.get("card[cvc]"):
            return error(400, "card_error", "Your card number is incorrect.")
        method = _id("pm")
        state.methods[method] = {"brand": "visa", "last4": number[-4:], "decline": number == DECLINED_TEST_CARD}
        return jsonify(id=method, card={"brand": "visa", "last4": number[-4:]})
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**`create_provider_app`, part 3 of 6.**

Step by step:

- Defines a helper function `create_customer()`.
  - If not (`secret_ok()`):
    - Gives back the result of calling `error(401, 'authentication_error', 'Invalid secret key')`.
  - Stores the result of calling `_id('cus')` in `customer`.
  - Calls `state.customers.add(customer)`.
  - Gives back the result of calling `jsonify(id=customer)`.
- Defines a helper function `create_method()`.
  - If not (`publishable_ok()`):
    - Gives back the result of calling `error(401, 'authentication_error', 'Invalid publishable key')`.
  - Stores the result of calling `request.form.get('card[number]', '').replace(' ', '')` in `number`.
  - If not (`luhn_valid(number)`) or not (`request.form.get('card[cvc]')`):
    - Gives back the result of calling `error(400, 'card_error', 'Your card number is incorrect.')`.
  - Stores the result of calling `_id('pm')` in `method`.
  - Stores the dictionary `{'brand': 'visa', 'last4': number[-4:], 'decline': number == DECLINED…` in `state.methods[method]`.
  - Gives back the result of calling `jsonify(id=method, card={'brand': 'visa', 'last4': number[-4:]})`.

`src/pci_scope/interfaces/provider_app.py` lines 122 to 151:

```python
    @app.post("/v1/payment_intents")
    def create_intent() -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        form = request.form
        if not form.get("amount", "").isdigit() or not form.get("currency"):
            return error(400, "invalid_request_error", "amount and currency are required")
        intent_id = _id("pi")
        intent: dict[str, Any] = {
            "id": intent_id,
            "client_secret": f"{intent_id}_secret_{secrets.token_hex(8)}",
            "amount": int(form["amount"]),
            "currency": form["currency"],
            "customer": form.get("customer"),
            "payment_method": form.get("payment_method"),
            "status": "requires_payment_method", "setup_future_usage": form.get("setup_future_usage"),
        }  # fmt: skip
        with state.lock:
            state.intents[intent_id] = intent
            if form.get("confirm") == "true":
                method = state.methods.get(form.get("payment_method", ""))
                if method is None or form.get("customer") not in state.customers or form.get("off_session") != "true":
                    return error(
                        400,
                        "invalid_request_error",
                        "a saved payment method and customer are required to charge off-session",
                    )
                intent["status"] = "requires_payment_method" if method["decline"] else "succeeded"
                emit("payment_intent.payment_failed" if method["decline"] else "payment_intent.succeeded", intent)
        return jsonify(_public(intent))
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**`create_provider_app`, part 4 of 6.**

Step by step:

- Defines a helper function `create_intent()`.
  - If not (`secret_ok()`):
    - Gives back the result of calling `error(401, 'authentication_error', 'Invalid secret key')`.
  - Stores `request.form` in `form`.
  - If not (`form.get('amount', '').isdigit()`) or not (`form.get('currency')`):
    - Gives back the result of calling `error(400, 'invalid_request_error', 'amount and currency are required')`.
  - Stores the result of calling `_id('pi')` in `intent_id`.
  - Declares `intent` as a `dict[str, Any]` and stores the dictionary `{'id': intent_id, 'client_secret': f'{intent_id}_secret_{secrets.toke…` in it.
  - Inside a `with` block that opens `state.lock`:
    - Stores `intent` in `state.intents[intent_id]`.
    - If `form.get('confirm')` equals `'true'`:
      - Stores the result of calling `state.methods.get(form.get('payment_method', ''))` in `method`.
      - If `method` is the same object as `None` or `form.get('customer')` is not in `state.customers` or `form.get('off_session')` is different from `'true'`:
        - Gives back the result of calling `error(400, 'invalid_request_error', 'a saved payment method and customer are required to …`.
      - Stores `'requires_payment_method'` if `method['decline']`, otherwise `'succeeded'` in `intent['status']`.
      - Calls `emit('payment_intent.payment_failed' if method['decline'] else 'payment_intent.succeeded', intent)`.

`src/pci_scope/interfaces/provider_app.py` lines 153 to 176:

```python
    @app.get("/v1/payment_intents/<intent_id>")
    def get_intent(intent_id: str) -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        intent = state.intents.get(intent_id)
        return jsonify(_public(intent)) if intent else error(404, "invalid_request_error", "No such payment_intent")

    @app.post("/v1/payment_intents/<intent_id>/confirm")
    def confirm(intent_id: str) -> tuple[Response, int] | Response:
        if not publishable_ok():
            return error(401, "authentication_error", "Invalid publishable key")
        with state.lock:
            intent = state.intents.get(intent_id)
            if intent is None or intent["client_secret"] != request.form.get("client_secret"):
                return error(404, "invalid_request_error", "No such payment_intent")
            method = state.methods.get(request.form.get("payment_method", ""))
            if method is None:
                return error(400, "invalid_request_error", "payment_method is required")
            intent["payment_method"] = request.form["payment_method"]
            intent["status"] = "requires_payment_method" if method["decline"] else "succeeded"
            emit("payment_intent.payment_failed" if method["decline"] else "payment_intent.succeeded", intent)
            if method["decline"]:
                return error(402, "card_error", "Your card was declined.")
        return jsonify(_public(intent))
```

**`create_provider_app`, part 5 of 6.**

Step by step:

- Defines a helper function `get_intent(intent_id)`.
  - If not (`secret_ok()`):
    - Gives back the result of calling `error(401, 'authentication_error', 'Invalid secret key')`.
  - Stores the result of calling `state.intents.get(intent_id)` in `intent`.
  - Gives back `jsonify(_public(intent))` if `intent`, otherwise `error(404, 'invalid_request_error', 'No…`.
- Defines a helper function `confirm(intent_id)`.
  - If not (`publishable_ok()`):
    - Gives back the result of calling `error(401, 'authentication_error', 'Invalid publishable key')`.
  - Inside a `with` block that opens `state.lock`:
    - Stores the result of calling `state.intents.get(intent_id)` in `intent`.
    - If `intent` is the same object as `None` or `intent['client_secret']` is different from `request.form.get('client_secret')`:
      - Gives back the result of calling `error(404, 'invalid_request_error', 'No such payment_intent')`.
    - Stores the result of calling `state.methods.get(request.form.get('payment_method', ''))` in `method`.
    - If `method` is the same object as `None`:
      - Gives back the result of calling `error(400, 'invalid_request_error', 'payment_method is required')`.
    - Stores `request.form['payment_method']` in `intent['payment_method']`.
    - Stores `'requires_payment_method'` if `method['decline']`, otherwise `'succeeded'` in `intent['status']`.
    - Calls `emit('payment_intent.payment_failed' if method['decline'] else 'payment_intent.succeeded', intent)`.
    - If `method['decline']`:
      - Gives back the result of calling `error(402, 'card_error', 'Your card was declined.')`.
  - Gives back the result of calling `jsonify(_public(intent))`.

`src/pci_scope/interfaces/provider_app.py` lines 178 to 189:

```python
    @app.post("/v1/refunds")
    def refund() -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        intent = state.intents.get(request.form.get("payment_intent", ""))
        if intent is None or intent["status"] != "succeeded":
            return error(400, "invalid_request_error", "only a succeeded payment can be refunded")
        refund_id = _id("re")
        state.refunds[refund_id] = intent["id"]
        return jsonify(id=refund_id, payment_intent=intent["id"])

    return app
```

**`create_provider_app`, part 6 of 6.**

Step by step:

- Defines a helper function `refund()`.
  - If not (`secret_ok()`):
    - Gives back the result of calling `error(401, 'authentication_error', 'Invalid secret key')`.
  - Stores the result of calling `state.intents.get(request.form.get('payment_intent', ''))` in `intent`.
  - If `intent` is the same object as `None` or `intent['status']` is different from `'succeeded'`:
    - Gives back the result of calling `error(400, 'invalid_request_error', 'only a succeeded payment can be refunded')`.
  - Stores the result of calling `_id('re')` in `refund_id`.
  - Stores `intent['id']` in `state.refunds[refund_id]`.
  - Gives back the result of calling `jsonify(id=refund_id, payment_intent=intent['id'])`.
- Gives back `app`.

`src/pci_scope/interfaces/provider_app.py` lines 192 to 232:

```python
ELEMENTS_JS = """\
// The provider's script. It runs in the merchant's page, creates an iframe served by the provider, and asks that frame
// to confirm the payment. The card is typed into the frame, so the merchant's page and server never see it.
(function () {
  var origin = new URL(document.currentScript.src).origin;
  window.Provider = function (publishableKey) {
    return {
      elements: function (options) {
        var frame = null;
        return {
          create: function () {
            return {
              mount: function (selector) {
                frame = document.createElement("iframe");
                frame.title = "Card details";
                frame.style.cssText = "border:0;width:100%;height:150px";
                frame.src = origin + "/frame?origin=" + encodeURIComponent(location.origin) +
                  "&client_secret=" + encodeURIComponent(options.clientSecret);
                document.querySelector(selector).appendChild(frame);
              },
            };
          },
          frame: function () { return frame; },
        };
      },
      confirmPayment: function (args) {
        var frame = args.elements.frame();
        window.addEventListener("message", function (event) {
          if (event.origin !== origin) { return; }
          if (event.data.status === "succeeded") {
            location.href = args.confirmParams.return_url + "?payment_intent=" + encodeURIComponent(event.data.id);
          } else {
            document.querySelector("#message").textContent = event.data.message || "The payment did not go through.";
          }
        });
        frame.contentWindow.postMessage({ type: "confirm" }, origin);
      },
    };
  };
})();
"""
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'// The provider\'s script. It runs in the merchant\'s page…` in `ELEMENTS_JS`.

`src/pci_scope/interfaces/provider_app.py` lines 234 to 263:

```python
FRAME_HTML = """\
<!doctype html>
<meta charset="utf-8">
<title>Card details</title>
<form id="card" autocomplete="off">
  <label>Card number <input id="number" inputmode="numeric" autocomplete="cc-number"></label>
  <label>Expiry <input id="expiry" placeholder="MM / YY" autocomplete="cc-exp"></label>
  <label>CVC <input id="cvc" inputmode="numeric" autocomplete="cc-csc"></label>
</form>
<script>
  var key = "__KEY__", secret = "__SECRET__";
  var intentId = secret.split("_secret_")[0];
  function form(values) { return new URLSearchParams(values).toString(); }
  window.addEventListener("message", async function (event) {
    if (!event.data || event.data.type !== "confirm") { return; }
    var parts = document.getElementById("expiry").value.split("/").map(function (p) { return p.trim(); });
    var headers = { "Content-Type": "application/x-www-form-urlencoded", "X-Publishable-Key": key };
    var method = await (await fetch("/v1/payment_methods", { method: "POST", headers: headers, body: form({
      "card[number]": document.getElementById("number").value,
      "card[exp_month]": parts[0] || "", "card[exp_year]": parts[1] || "",
      "card[cvc]": document.getElementById("cvc").value }) })).json();
    if (method.error) { parent.postMessage({ status: "failed", message: method.error.message }, event.origin); return; }
    var result = await (await fetch("/v1/payment_intents/" + intentId + "/confirm", { method: "POST", headers: headers,
      body: form({ client_secret: secret, payment_method: method.id }) })).json();
    parent.postMessage(
      result.error ? { status: "failed", message: result.error.message } : { status: result.status, id: result.id },
      event.origin);
  });
</script>
"""
```

These module-level lines:

- Stores the text `'<!doctype html>\n<meta charset="utf-8">\n<title>Card detai…` in `FRAME_HTML`.

### `src/pci_scope/interfaces/servers.py`

`src/pci_scope/interfaces/servers.py` lines 1 to 11:

```python
"""Run the three apps as real HTTP servers on local ports, in threads, and stop them cleanly."""

from __future__ import annotations

import logging
import socket
import threading
from types import TracebackType

from flask import Flask
from werkzeug.serving import BaseWSGIServer, make_server
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Run the three apps as real HTTP servers on local ports, in threads, and stop them cleanly.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `logging`.
- It imports module `socket`.
- It imports module `threading`.
- From `types` it takes `TracebackType`.
- From `flask` it takes `Flask`.
- From `werkzeug.serving` it takes `BaseWSGIServer, make_server`.

`src/pci_scope/interfaces/servers.py` lines 14 to 18:

```python
def free_port() -> int:
    """A port nobody is listening on right now."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `obj[key]` looks a value up by key or position.

**Function `free_port`.** A port nobody is listening on right now.

It gives back a `int`.

Step by step:

- Inside a `with` block that opens `socket.socket()` (named `probe`):
  - Calls `probe.bind(('127.0.0.1', 0))`.
  - Gives back the result of calling `int(probe.getsockname()[1])`.

`src/pci_scope/interfaces/servers.py` lines 21 to 41:

```python
class LocalServer:
    """A Flask app served on 127.0.0.1:<port> until the context exits; shutdown waits for in-flight requests."""

    def __init__(self, app: Flask, port: int) -> None:
        logging.getLogger("werkzeug").setLevel(
            logging.WARNING
        )  # no access log: a URL is one more place for data to land
        self._server: BaseWSGIServer = make_server("127.0.0.1", port, app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self.url = f"http://127.0.0.1:{port}"

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

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.

**Class `LocalServer`**. A Flask app served on 127.0.0.1:<port> until the context exits; shutdown waits for in-flight requests.

Its methods, in order:

**Method `__init__` of class `LocalServer`.**

It takes: `app` (a `Flask`); `port` (a `int`).

It gives back a `None`.

Step by step:

- Calls `logging.getLogger('werkzeug').setLevel(logging.WARNING)`.
- Declares `self._server` as a `BaseWSGIServer` and stores the result of calling `make_server('127.0.0.1', port, app, threaded=True)` in it.
- Stores the result of calling `threading.Thread(target=self._server.serve_forever, daemon=True)` in `self._thread`.
- Stores a text built with values filled in (`f'http://127.0.0.1:{port}'`) in `self.url`.

**Method `__enter__` of class `LocalServer`.**

It gives back a `LocalServer`.

Step by step:

- Calls `self._thread.start()`.
- Gives back `self`.

**Method `__exit__` of class `LocalServer`.**

It takes: `kind` (a `type[BaseException] | None`); `value` (a `BaseException | None`); `trace` (a `TracebackType | None`).

It gives back a `None`.

Step by step:

- Calls `self._server.shutdown()`.
- Calls `self._thread.join(timeout=5)`.
- Calls `self._server.server_close()`.

## Try it yourself

```bash
.venv/bin/python -c "import pci_scope.interfaces.browser_sim; print(pci_scope.interfaces.browser_sim.__doc__)"
```
Prints the module's description: `A scripted browser: it makes the requests a customer's browser makes during a checkout and records them as a HAR.`

```bash
.venv/bin/python -c "import pci_scope.interfaces.cli; print(pci_scope.interfaces.cli.__doc__)"
```
Prints the module's description: ``pci-scope`: the scenario, the scope, the scanner, the verification. Exit codes: 0 ok, 1 findings, 2 bad input.`

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check src/pci_scope/interfaces/__init__.py src/pci_scope/interfaces/browser_sim.py src/pci_scope/interfaces/cli.py src/pci_scope/interfaces/demo.py src/pci_scope/interfaces/factories.py src/pci_scope/interfaces/merchant_app.py
```
Prints `All checks passed!`.

```bash
grep -c "^def \|^class \|    def " src/pci_scope/interfaces/browser_sim.py
```
Counts the functions, methods and classes in `src/pci_scope/interfaces/browser_sim.py`.

## Mistakes people make

- Putting rules in a route or a command handler. They call the use cases.
- Returning raw error text to the caller. Named errors map to fixed messages and codes.
- Creating adapters deep inside the code instead of here, which makes testing hard.

## Check yourself

1. What is `Reply` for?
   **Answer:** What came back.
2. What is `PaymentRun` for?
   **Answer:** The requests made, and what the page and the payment turned out to be.
3. What is `Browser` for?
   **Answer:** Makes HTTP requests and keeps the log of them.
4. What is `pay_with_hosted_fields` for?
   **Answer:** The redesigned checkout, start to finish, with the published test card typed into the provider's frame.
5. What is `pay_on_naive_checkout` for?
   **Answer:** The "before": the card posted to the merchant's own server.

## Further reading

- Python 3.12 tutorial, classes: <https://docs.python.org/3.12/tutorial/classes.html>
- Python 3.12 language reference: <https://docs.python.org/3.12/reference/>
- Type hints: <https://docs.python.org/3.12/library/typing.html>
