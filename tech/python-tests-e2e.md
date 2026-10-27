# The tests (e2e)

## What it is

The pytest tests in `tests/e2e`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/e2e/test_scenario.py` | 74 lines. The lesson's scenario against real local servers: the naive checkout, the redesign, the proof and the pack. |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/e2e/test_scenario.py`

`tests/e2e/test_scenario.py` lines 1 to 15:

```python
"""The lesson's scenario against real local servers: the naive checkout, the redesign, the proof and the pack."""

from __future__ import annotations

import json
import shutil

import pytest

from pci_scope.domain.card import TEST_CARD
from pci_scope.infrastructure.settings import load_settings
from pci_scope.interfaces.cli import main
from pci_scope.interfaces.demo import run_demo
from pci_scope.interfaces.servers import free_port
from tests.conftest import REPOSITORY_ROOT
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The lesson's scenario against real local servers: the naive checkout, the redesign, the proof and the pack.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- It imports module `shutil`.
- It imports module `pytest`.
- From `pci_scope.domain.card` it takes `TEST_CARD`.
- From `pci_scope.infrastructure.settings` it takes `load_settings`.
- From `pci_scope.interfaces.cli` it takes `main`.
- From `pci_scope.interfaces.demo` it takes `run_demo`.
- From `pci_scope.interfaces.servers` it takes `free_port`.
- From `tests.conftest` it takes `REPOSITORY_ROOT`.

`tests/e2e/test_scenario.py` lines 17 to 17:

```python
pytestmark = pytest.mark.e2e
```

These module-level lines:

- Stores `pytest.mark.e2e` in `pytestmark`.

`tests/e2e/test_scenario.py` lines 20 to 35:

```python
@pytest.fixture
def settings(tmp_path):
    ports = [free_port() for _ in range(3)]
    env = {
        "PROVIDER_BASE_URL": f"http://127.0.0.1:{ports[0]}",
        "PROVIDER_SECRET_KEY": "sk_test_e2e",
        "PROVIDER_PUBLISHABLE_KEY": "pk_test_e2e",
        "WEBHOOK_SECRET": "w" * 32,
        "MERCHANT_BASE_URL": f"http://127.0.0.1:{ports[1]}",
        "NAIVE_BASE_URL": f"http://127.0.0.1:{ports[2]}",
        "DATABASE_PATH": str(tmp_path / "state" / "merchant.db"),
        "NAIVE_LOG_PATH": str(tmp_path / "state" / "naive" / "requests.log"),
        "STATE_DIR": str(tmp_path / "state"),
        "EVIDENCE_DIR": str(tmp_path / "evidence"),
    }
    return load_settings(env), env
```

> **In plain words.** A **fixture** is a helper function marked `@pytest.fixture`. A test that names it as a parameter receives its return value, prepared fresh for that test.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `tmp_path` is a built-in pytest fixture: a fresh, empty temporary folder (a `Path`) that is removed after the test.

**Function `settings`.**

It takes: `tmp_path`.

Decorators: `@pytest.fixture`.

Step by step:

- Stores a new list made by a loop (`[free_port() for _ in range(3)]`) in `ports`.
- Stores the dictionary `{'PROVIDER_BASE_URL': f'http://127.0.0.1:{ports[0]}', 'PROVIDER_SECRE…` in `env`.
- Gives back the tuple `(load_settings(env), env)`.

`tests/e2e/test_scenario.py` lines 38 to 75:

```python
def test_the_lessons_scenario_end_to_end(settings, monkeypatch, capsys):
    loaded, env = settings
    result = run_demo(loaded, REPOSITORY_ROOT)

    # Done when 1 and the problem: the naive checkout puts the card in its log.
    assert result.before.exit_code == 1
    assert "FOUND card number 424242******4242" in result.before.text

    # Done when 2: a test payment succeeds and the merchant's log, database and backup hold tokens only.
    assert result.run.final_status == 200
    assert result.run.final_text == f"payment {result.run.intent_id}: succeeded"
    assert result.after.exit_code == 0
    assert result.after.artifacts == 3
    assert set(result.order_statuses.values()) == {"succeeded", "refunded"}

    # Done when 3: the capture shows the card fields went to the provider only.
    pack = loaded.evidence_dir
    har = json.loads((pack / "payment.har").read_text())["log"]["entries"]
    to_merchant = [e for e in har if e["request"]["url"].startswith(loaded.merchant_base_url)]
    to_provider = [e for e in har if e["request"]["url"].startswith(loaded.provider_base_url)]
    assert to_merchant
    assert not any("card" in e["request"]["postData"]["text"].lower() for e in to_merchant)
    assert any("card%5Bnumber%5D=[redacted]" in e["request"]["postData"]["text"] for e in to_provider)
    assert TEST_CARD not in (pack / "payment.har").read_text()

    # Done when 5: the scope shrank, and the page and its pipeline stay in scope.
    change = (pack / "scope-change.md").read_text()
    assert "Before: 9 systems and 3 teams in scope." in change
    assert "After: 3 systems and 2 teams in scope." in change

    # The pack verifies; a hand edit and a card in the capture are caught.
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    assert main(["verify"]) == 0
    capsys.readouterr()
    (pack / "route-check.txt").write_text("edited by hand\n")
    assert main(["verify"]) == 1
    assert "EVP003" in capsys.readouterr().out
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.
> **In plain words.** `monkeypatch` is a built-in pytest fixture that changes something (an environment variable, an attribute) for this test only and undoes it afterwards.
> **In plain words.** `capsys` is a built-in pytest fixture that captures what the program prints, so the test can read it with `capsys.readouterr()`.

**Test `test_the_lessons_scenario_end_to_end`** checks: the lessons scenario end to end.

It takes: `settings`; `monkeypatch`; `capsys`.

Step by step:

- Unpacks `settings` into `(loaded, env)`.
- Stores the result of calling `run_demo(loaded, REPOSITORY_ROOT)` in `result`.
- Checks that `result.before.exit_code` equals `1`; if not, the test fails.
- Checks that `'FOUND card number 424242******4242'` is in `result.before.text`; if not, the test fails.
- Checks that `result.run.final_status` equals `200`; if not, the test fails.
- Checks that `result.run.final_text` equals `f'payment {result.run.intent_id}: succeeded'`; if not, the test fails.
- Checks that `result.after.exit_code` equals `0`; if not, the test fails.
- Checks that `result.after.artifacts` equals `3`; if not, the test fails.
- Checks that `set(result.order_statuses.values())` equals `{'succeeded', 'refunded'}`; if not, the test fails.
- Stores `loaded.evidence_dir` in `pack`.
- Stores `json.loads((pack / 'payment.har').read_text())['log']['entries']` in `har`.
- Stores a new list made by a loop (`[e for e in har if e['request']['url'].startswith(loaded.merchant_bas…`) in `to_merchant`.
- Stores a new list made by a loop (`[e for e in har if e['request']['url'].startswith(loaded.provider_bas…`) in `to_provider`.
- Checks that `to_merchant`; if not, the test fails.
- Checks that not (`any(('card' in e['request']['postData']['text'].lower() for e in to_m…`); if not, the test fails.
- Checks that `any(('card%5Bnumber%5D=[redacted]' in e['request']['postData']['text'…`; if not, the test fails.
- Checks that `TEST_CARD` is not in `(pack / 'payment.har').read_text()`; if not, the test fails.
- Stores the result of calling `(pack / 'scope-change.md').read_text()` in `change`.
- Checks that `'Before: 9 systems and 3 teams in scope.'` is in `change`; if not, the test fails.
- Checks that `'After: 3 systems and 2 teams in scope.'` is in `change`; if not, the test fails.
- For each `(name, value)` in the result of calling `env.items()`:
  - Calls `monkeypatch.setenv(name, value)`.
- Checks that `main(['verify'])` equals `0`; if not, the test fails.
- Calls `capsys.readouterr()`.
- Calls `(pack / 'route-check.txt').write_text('edited by hand\n')`.
- Checks that `main(['verify'])` equals `1`; if not, the test fails.
- Checks that `'EVP003'` is in `capsys.readouterr().out`; if not, the test fails.

`tests/e2e/test_scenario.py` lines 78 to 96:

```python
def test_a_card_sent_to_the_merchant_makes_the_capture_fail_verification(settings, monkeypatch, capsys):
    loaded, env = settings
    run_demo(loaded, REPOSITORY_ROOT)
    pack = loaded.evidence_dir
    har = json.loads((pack / "payment.har").read_text())
    har["log"]["entries"][0]["request"]["postData"]["text"] = "card_number=4242424242424242"
    tampered = json.dumps(har)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    shutil.copy(pack / "manifest.json", pack / "manifest.bak")
    (pack / "payment.har").write_text(tampered)
    manifest = json.loads((pack / "manifest.json").read_text())
    from pci_scope.domain.evidence import digest

    manifest["payment.har"]["sha256"] = digest(tampered)
    (pack / "manifest.json").write_text(json.dumps(manifest))
    (pack / "manifest.bak").unlink()
    assert main(["verify"]) == 1
    assert "carries card data" in capsys.readouterr().out
```

**Test `test_a_card_sent_to_the_merchant_makes_the_capture_fail_verification`** checks: a card sent to the merchant makes the capture fail verification.

It takes: `settings`; `monkeypatch`; `capsys`.

Step by step:

- Unpacks `settings` into `(loaded, env)`.
- Calls `run_demo(loaded, REPOSITORY_ROOT)`.
- Stores `loaded.evidence_dir` in `pack`.
- Stores the result of calling `json.loads((pack / 'payment.har').read_text())` in `har`.
- Stores the text `'card_number=4242424242424242'` in `har['log']['entries'][0]['request']['postData']['text']`.
- Stores the result of calling `json.dumps(har)` in `tampered`.
- For each `(name, value)` in the result of calling `env.items()`:
  - Calls `monkeypatch.setenv(name, value)`.
- Calls `shutil.copy(pack / 'manifest.json', pack / 'manifest.bak')`.
- Calls `(pack / 'payment.har').write_text(tampered)`.
- Stores the result of calling `json.loads((pack / 'manifest.json').read_text())` in `manifest`.
- Imports `from pci_scope.domain.evidence import digest`.
- Stores the result of calling `digest(tampered)` in `manifest['payment.har']['sha256']`.
- Calls `(pack / 'manifest.json').write_text(json.dumps(manifest))`.
- Calls `(pack / 'manifest.bak').unlink()`.
- Checks that `main(['verify'])` equals `1`; if not, the test fails.
- Checks that `'carries card data'` is in `capsys.readouterr().out`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/e2e
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check tests/e2e/test_scenario.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_the_lessons_scenario_end_to_end` check?
   **Answer:** it checks: the lessons scenario end to end.
2. What does the test `test_a_card_sent_to_the_merchant_makes_the_capture_fail_verification` check?
   **Answer:** it checks: a card sent to the merchant makes the capture fail verification.
3. What is a docstring?
   **Answer:** A text in triple quotes at the start of a module, class or function that describes it.
4. What does `frozen=True` do on a dataclass?
   **Answer:** It forbids changing a field after the object is created.
5. What does a type hint do at run time?
   **Answer:** Nothing; mypy reads hints before the program runs.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
