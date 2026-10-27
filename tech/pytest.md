# pytest

## What it is

A **test** is a small function that runs part of the program and states what must be true afterwards, with the
word `assert`. **pytest** is a tool that finds the test functions in a folder, runs them, and reports which passed
and which failed. A **fixture** is a helper function that prepares something a test needs (a temporary folder, a
sample object) and is handed to the test by name.

## Why this repository uses it

The security claim is "card data never reaches the merchant". The tests check it two ways. The unit tests cover each rule with
fakes: the card patterns and the Luhn check, the scope calculator, the signed webhooks, the HAR analysis, the evidence rules. The
end-to-end test starts **real HTTP servers** (the provider, the merchant and the naive checkout) on local ports and runs the whole
scenario against them.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/**` | Unit tests per layer: `domain`, `application`, `infrastructure`, `interfaces`. |
| `tests/e2e/test_scenario.py` | The scenario against real local servers, marked `e2e`. |
| `tests/conftest.py` | Shared helpers. |
| `pyproject.toml` `[tool.pytest.ini_options]` | Where to look, the options to always use, the `e2e` marker. |
| `Makefile` `test`, `test-e2e` | Run the unit tests under coverage; run the end-to-end test. |

## How it works underneath

1. pytest starts, reads `pyproject.toml`, and walks the folders in `testpaths`.
2. It imports each file named `test_*.py`. Each function whose name starts with `test_` is one test.
3. For each test it looks at the function's parameter names. A parameter named `tmp_path` or `capsys` is a built-in
   fixture; a name defined with `@pytest.fixture` in the file or in `conftest.py` is a custom one. pytest builds
   those values and passes them in.
4. It runs the function. If every `assert` holds and nothing is raised, the test passes. pytest rewrites `assert`
   lines when it imports a test file, so a failure shows both sides of the comparison.
5. After the run it prints one dot per passing test, then a summary line.

## Walkthrough of this repository's use

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
```

- `testpaths = ["tests"]`: when run with no arguments, look only in `tests/`.
- `addopts = "-ra --strict-markers"`: options added to every run. `-ra` prints a short reason line for every
  test that is not a plain pass (skipped, failed, error). `--strict-markers` turns an unknown `@pytest.mark.xyz`
  into an error instead of a silent typo.

`tests/conftest.py`:

```python
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
```

`__file__` is the path of this file. `.resolve()` makes it absolute. `.parents[1]` is two levels up (the folder
holding `tests/`), which is the repository root. Tests use it to find the real `docs/` folder.

`tests/conftest.py`:

```python
from __future__ import annotations

from pathlib import Path

from pci_scope.domain.payment import Intent, Order, PaymentError

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SECRET = "whsec_unit_test_secret_value_0123456789abcdef"


class FakeProvider:
    """Records calls and answers like a provider: intents succeed unless the method is marked declined."""
```

Shared test helpers for the unit tests.

`tests/unit/domain/test_card_scope_webhook_har.py`:

```python
def test_published_test_numbers_pass_the_luhn_check(number):
    assert luhn_valid(number)


@pytest.mark.parametrize("number", ["4242424242424241", "1234567890123456", "abcd", ""])
```

The simplest kind of test: call a function, compare the result with the expected value using `assert`.

`tests/e2e/test_scenario.py`:

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

`@pytest.fixture` marks a function as a fixture: a test that names it as a parameter receives its value. A fixture with `yield` sets something up before the yield and tears it down after the test. `tmp_path` is a fresh empty folder per test, deleted afterwards. `monkeypatch.setenv` changes an
environment variable for this test only and undoes it at the end. The type hints (`Path`, `pytest.MonkeyPatch`)
are optional for pytest, but help the reader.

`tests/unit/interfaces/test_apps.py`:

```python
def test_a_payment_with_the_test_card_succeeds_and_the_provider_sends_a_signed_event(provider):
    _, method, result = pay(provider)
    assert result.status_code == 200
    assert result.get_json()["status"] == "succeeded"
    assert method["id"].startswith("pm_")
    url, body, signature = provider.delivered[0]
    assert url == "http://merchant/webhook"
    assert json.loads(body)["type"] == "payment_intent.succeeded"
```

This test damages one copied document, runs the real command, and checks the exit code (`== 1`) and the output
with `capsys`, the fixture that captures what the program prints. The tests prove each rule fails when the document
is damaged, not only that the good document passes.

`tests/unit/domain/test_card_scope_webhook_har.py`:

```python
@pytest.mark.parametrize("number", [TEST_CARD, "4000000000000002", "378282246310005", "5555555555554444"])
def test_published_test_numbers_pass_the_luhn_check(number):
    assert luhn_valid(number)


@pytest.mark.parametrize("number", ["4242424242424241", "1234567890123456", "abcd", ""])
def test_other_numbers_do_not(number):
    assert not luhn_valid(number)
```

`@pytest.mark.parametrize` runs the same test body once per row of data. A failure names the row that broke.

The `markers = [...]` line **registers** the marker `e2e`. `make test-e2e` selects it with `-m e2e`. Because of `--strict-markers`, a misspelled marker is an error, not a silent skip.

## Try it yourself

```bash
.venv/bin/pytest -q
```
Prints rows of dots and a summary like `N passed in` some seconds. The tests include real HTTP servers on local ports (see `threads-and-sockets.md`).

```bash
.venv/bin/pytest --collect-only -q tests/unit/domain/test_card_scope_webhook_har.py
```
Lists the test names without running them, one `path::test_name` per line.

```bash
.venv/bin/pytest -q -k webhook
```
Runs only tests whose name contains `webhook`: the tests about signed webhooks.

```bash
.venv/bin/pytest -q tests/unit/domain/test_card_scope_webhook_har.py -x -vv
```
`-x` stops at the first failure; `-vv` shows each test name and result.

```bash
.venv/bin/pytest --fixtures -q | grep -E "tmp_path|capsys|monkeypatch" | head
```
Shows the built-in fixtures this repository uses.

## Mistakes people make

- **Tests that depend on each other's order.** Each test here builds its own data (a fresh `tmp_path`).
- **Asserting only the happy path.** The tests here also break a document on purpose and check the rule code.
- **Forgetting `test_` in a name**, so the test never runs. Check the count in the summary.
- **Editing the real `docs/` from a test.** The CLI tests copy `docs/` to a temporary folder first.

## Check yourself

1. How does pytest know which functions are tests?
   **Answer:** Files named `test_*.py`, functions named `test_*`.
2. What does `tmp_path` give a test?
   **Answer:** A fresh, empty temporary folder that is removed afterwards.
3. What does `-ra` print?
   **Answer:** A short summary line for every test that is not a plain pass.
4. Why does the CLI test copy `docs/` first?
   **Answer:** So the test can damage a document without changing the real repository.
5. What does `parametrize` do?
   **Answer:** It runs one test function several times with different data.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- Configuration (`pyproject.toml`): <https://docs.pytest.org/en/stable/reference/customize.html>
