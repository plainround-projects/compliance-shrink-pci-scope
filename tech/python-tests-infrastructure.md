# The tests (infrastructure)

## What it is

The pytest tests in `tests/unit/infrastructure`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/infrastructure/test_adapters.py` | 189 lines.  |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/unit/infrastructure/test_adapters.py`

`tests/unit/infrastructure/test_adapters.py` lines 1 to 21:

```python
import json
import socket
import sqlite3
import threading
from contextlib import closing
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from pci_scope.domain.card import TEST_CARD
from pci_scope.domain.payment import PaymentError
from pci_scope.infrastructure.artifacts import MerchantArtifacts, NaiveArtifacts, PathArtifacts
from pci_scope.infrastructure.catalog import CatalogError, load_inventory, load_requirements
from pci_scope.infrastructure.evidence_store import FileEvidenceStore
from pci_scope.infrastructure.logging_setup import JsonFormatter
from pci_scope.infrastructure.provider_http import HttpProvider
from pci_scope.infrastructure.settings import SettingsError, load_settings
from pci_scope.infrastructure.sqlite_orders import SqliteOrders
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app
from pci_scope.interfaces.servers import LocalServer, free_port
from tests.conftest import REPOSITORY_ROOT
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `json`.
- It imports module `socket`.
- It imports module `sqlite3`.
- It imports module `threading`.
- From `contextlib` it takes `closing`.
- From `http.server` it takes `BaseHTTPRequestHandler, HTTPServer`.
- It imports module `pytest`.
- From `pci_scope.domain.card` it takes `TEST_CARD`.
- From `pci_scope.domain.payment` it takes `PaymentError`.
- From `pci_scope.infrastructure.artifacts` it takes `MerchantArtifacts, NaiveArtifacts, PathArtifacts`.
- From `pci_scope.infrastructure.catalog` it takes `CatalogError, load_inventory, load_requirements`.
- From `pci_scope.infrastructure.evidence_store` it takes `FileEvidenceStore`.
- From `pci_scope.infrastructure.logging_setup` it takes `JsonFormatter`.
- From `pci_scope.infrastructure.provider_http` it takes `HttpProvider`.
- From `pci_scope.infrastructure.settings` it takes `SettingsError, load_settings`.
- From `pci_scope.infrastructure.sqlite_orders` it takes `SqliteOrders`.
- From `pci_scope.interfaces.provider_app` it takes `ProviderState, create_provider_app`.
- From `pci_scope.interfaces.servers` it takes `LocalServer, free_port`.
- From `tests.conftest` it takes `REPOSITORY_ROOT`.

`tests/unit/infrastructure/test_adapters.py` lines 23 to 29:

```python
ENV = {
    "PROVIDER_BASE_URL": "http://127.0.0.1:5001/",
    "PROVIDER_SECRET_KEY": "sk_test_abc",
    "PROVIDER_PUBLISHABLE_KEY": "pk_test_abc",
    "WEBHOOK_SECRET": "w" * 32,
    "MERCHANT_BASE_URL": "http://127.0.0.1:5000",
}
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the dictionary `{'PROVIDER_BASE_URL': 'http://127.0.0.1:5001/', 'PROVIDER_SECRET_KEY'…` in `ENV`.

`tests/unit/infrastructure/test_adapters.py` lines 32 to 36:

```python
def test_settings_strip_trailing_slashes_and_apply_defaults():
    settings = load_settings(ENV)
    assert settings.provider_base_url == "http://127.0.0.1:5001"
    assert settings.naive_base_url == "http://127.0.0.1:5002"
    assert str(settings.database_path) == "state/merchant.db"
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_settings_strip_trailing_slashes_and_apply_defaults`** checks: settings strip trailing slashes and apply defaults.

Step by step:

- Stores the result of calling `load_settings(ENV)` in `settings`.
- Checks that `settings.provider_base_url` equals `'http://127.0.0.1:5001'`; if not, the test fails.
- Checks that `settings.naive_base_url` equals `'http://127.0.0.1:5002'`; if not, the test fails.
- Checks that `str(settings.database_path)` equals `'state/merchant.db'`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 39 to 52:

```python
@pytest.mark.parametrize(
    "env",
    [
        {},
        {**ENV, "PROVIDER_SECRET_KEY": "sk_live_abc"},
        {**ENV, "PROVIDER_PUBLISHABLE_KEY": "pk_live_abc"},
        {**ENV, "WEBHOOK_SECRET": "short"},
        {**ENV, "LOG_LEVEL": "LOUD"},
        {key: value for key, value in ENV.items() if key != "MERCHANT_BASE_URL"},
    ],
)
def test_live_keys_and_missing_values_are_refused(env):
    with pytest.raises(SettingsError):
        load_settings(env)
```

> **In plain words.** `@pytest.mark.parametrize` runs the same test function once for each row of data given; a failure names the row that broke.
> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Test `test_live_keys_and_missing_values_are_refused`** checks: live keys and missing values are refused.

It takes: `env`.

Decorators: `@pytest.mark.parametrize('env', [{}, {**ENV, 'PROVIDER_SECRET_KEY': 's…`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(SettingsError)`:
  - Calls `load_settings(env)`.

`tests/unit/infrastructure/test_adapters.py` lines 55 to 70:

```python
def test_the_order_table_holds_tokens_and_refuses_a_card_number(tmp_path):
    orders = SqliteOrders(tmp_path / "m.db")
    orders.initialize((REPOSITORY_ROOT / "sql" / "001_schema.sql").read_text())
    created = orders.create("pi_" + "a" * 24, 1900, "eur", "cus_" + "b" * 24)
    assert (created.status, created.id) == ("pending", 1)
    orders.update(created.payment_intent_id, "succeeded", "pm_" + "c" * 24)
    found = orders.find(created.payment_intent_id)
    assert found is not None
    assert (found.status, found.payment_method_id) == ("succeeded", "pm_" + "c" * 24)
    assert orders.find("pi_" + "z" * 24) is None
    with pytest.raises(sqlite3.IntegrityError):
        orders.update(created.payment_intent_id, "succeeded", TEST_CARD)
    with pytest.raises(sqlite3.IntegrityError):
        orders.create(TEST_CARD, 1900, "eur", "")
    with pytest.raises(ValueError, match="unknown status"):
        orders.update(created.payment_intent_id, "paid-ish", "")
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `tmp_path` is a built-in pytest fixture: a fresh, empty temporary folder (a `Path`) that is removed after the test.

**Test `test_the_order_table_holds_tokens_and_refuses_a_card_number`** checks: the order table holds tokens and refuses a card number.

It takes: `tmp_path`.

Step by step:

- Stores the result of calling `SqliteOrders(tmp_path / 'm.db')` in `orders`.
- Calls `orders.initialize((REPOSITORY_ROOT / 'sql' / '001_schema.sql').read_text())`.
- Stores the result of calling `orders.create('pi_' + 'a' * 24, 1900, 'eur', 'cus_' + 'b' * 24)` in `created`.
- Checks that `(created.status, created.id)` equals `('pending', 1)`; if not, the test fails.
- Calls `orders.update(created.payment_intent_id, 'succeeded', 'pm_' + 'c' * 24)`.
- Stores the result of calling `orders.find(created.payment_intent_id)` in `found`.
- Checks that `found` is not the same object as `None`; if not, the test fails.
- Checks that `(found.status, found.payment_method_id)` equals `('succeeded', 'pm_' + 'c' * 24)`; if not, the test fails.
- Checks that `orders.find('pi_' + 'z' * 24)` is the same object as `None`; if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(sqlite3.IntegrityError)`:
  - Calls `orders.update(created.payment_intent_id, 'succeeded', TEST_CARD)`.
- Expects the steps inside to raise the error in `pytest.raises(sqlite3.IntegrityError)`:
  - Calls `orders.create(TEST_CARD, 1900, 'eur', '')`.
- Expects the steps inside to raise the error in `pytest.raises(ValueError, match='unknown status')`:
  - Calls `orders.update(created.payment_intent_id, 'paid-ish', '')`.

`tests/unit/infrastructure/test_adapters.py` lines 73 to 83:

```python
def test_the_order_table_reports_its_columns_rows_and_dump(tmp_path):
    orders = SqliteOrders(tmp_path / "m.db")
    orders.initialize(
        (REPOSITORY_ROOT / "sql" / "001_schema.sql").read_text()
        + (REPOSITORY_ROOT / "sql" / "002_seed.sql").read_text()
    )
    names = [name for name, _ in orders.columns()]
    assert names[:3] == ["id", "payment_intent_id", "amount_cents"]
    assert names[-2:] == ["payment_method_id", "created_at"]
    assert len(orders.rows()) == 2
    assert "pm_0123456789abcdef01234567" in orders.dump()
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Test `test_the_order_table_reports_its_columns_rows_and_dump`** checks: the order table reports its columns rows and dump.

It takes: `tmp_path`.

Step by step:

- Stores the result of calling `SqliteOrders(tmp_path / 'm.db')` in `orders`.
- Calls `orders.initialize((REPOSITORY_ROOT / 'sql' / '001_schema.sql').read_text() + (REPOSITORY_ROOT / 'sql' / '002_…`.
- Stores a new list made by a loop (`[name for name, _ in orders.columns()]`) in `names`.
- Checks that `names[:3]` equals `['id', 'payment_intent_id', 'amount_cents']`; if not, the test fails.
- Checks that `names[-2:]` equals `['payment_method_id', 'created_at']`; if not, the test fails.
- Checks that `len(orders.rows())` equals `2`; if not, the test fails.
- Checks that `'pm_0123456789abcdef01234567'` is in `orders.dump()`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 86 to 98:

```python
def test_the_merchant_artifacts_cover_logs_backups_and_the_database_dump_but_skip_named_folders(tmp_path):
    (tmp_path / "merchant").mkdir()
    (tmp_path / "merchant" / "app.log").write_text("created payment")
    (tmp_path / "backups").mkdir()
    (tmp_path / "backups" / "b.sql").write_text("INSERT")
    (tmp_path / "naive").mkdir()
    (tmp_path / "naive" / "requests.log").write_text(TEST_CARD)
    (tmp_path / "m.db").write_bytes(b"binary")
    names = [
        name for name, _ in MerchantArtifacts(tmp_path, lambda: "DUMP", tmp_path / "m.db", skip=("naive",)).artifacts()
    ]
    assert names == ["m.db (SQL dump)", "backups/b.sql", "merchant/app.log"]
    assert "naive/requests.log" in [name for name, _ in MerchantArtifacts(tmp_path).artifacts()]
```

> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Test `test_the_merchant_artifacts_cover_logs_backups_and_the_database_dump_but_skip_named_folders`** checks: the merchant artifacts cover logs backups and the database dump but skip named folders.

It takes: `tmp_path`.

Step by step:

- Calls `(tmp_path / 'merchant').mkdir()`.
- Calls `(tmp_path / 'merchant' / 'app.log').write_text('created payment')`.
- Calls `(tmp_path / 'backups').mkdir()`.
- Calls `(tmp_path / 'backups' / 'b.sql').write_text('INSERT')`.
- Calls `(tmp_path / 'naive').mkdir()`.
- Calls `(tmp_path / 'naive' / 'requests.log').write_text(TEST_CARD)`.
- Calls `(tmp_path / 'm.db').write_bytes(b'binary')`.
- Stores a new list made by a loop (`[name for name, _ in MerchantArtifacts(tmp_path, lambda: 'DUMP', tmp_…`) in `names`.
- Checks that `names` equals `['m.db (SQL dump)', 'backups/b.sql', 'merchant/ap…`; if not, the test fails.
- Checks that `'naive/requests.log'` is in `[name for name, _ in MerchantArtifacts(tmp_path).…`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 101 to 109:

```python
def test_the_naive_and_path_artifacts(tmp_path):
    log = tmp_path / "requests.log"
    assert list(NaiveArtifacts(log).artifacts()) == []
    log.write_text("x")
    assert list(NaiveArtifacts(log).artifacts()) == [("requests.log", "x")]
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "a.txt").write_text("a")
    assert [text for _, text in PathArtifacts([folder, log]).artifacts()] == ["a", "x"]
```

**Test `test_the_naive_and_path_artifacts`** checks: the naive and path artifacts.

It takes: `tmp_path`.

Step by step:

- Stores `tmp_path / 'requests.log'` in `log`.
- Checks that `list(NaiveArtifacts(log).artifacts())` equals `[]`; if not, the test fails.
- Calls `log.write_text('x')`.
- Checks that `list(NaiveArtifacts(log).artifacts())` equals `[('requests.log', 'x')]`; if not, the test fails.
- Stores `tmp_path / 'f'` in `folder`.
- Calls `folder.mkdir()`.
- Calls `(folder / 'a.txt').write_text('a')`.
- Checks that `[text for _, text in PathArtifacts([folder, log])…` equals `['a', 'x']`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 112 to 123:

```python
def test_the_evidence_store_writes_reads_and_records_hashes(tmp_path):
    from datetime import UTC, datetime

    store = FileEvidenceStore(tmp_path / "evidence")
    now = datetime(2026, 10, 27, tzinfo=UTC)
    store.write("a.txt", "hello\n", "P1", now)
    assert store.read_all() == {"a.txt": "hello\n", "manifest.json": store.read_all()["manifest.json"]}
    entry = store.manifest()["a.txt"]
    assert (entry.requirement, entry.produced_at, len(entry.sha256)) == ("P1", now, 64)
    assert FileEvidenceStore(tmp_path / "none").read_all() == {}
    with pytest.raises(ValueError, match="directly in"):
        store.write("../x", "x", "P1", now)
```

**Test `test_the_evidence_store_writes_reads_and_records_hashes`** checks: the evidence store writes reads and records hashes.

It takes: `tmp_path`.

Step by step:

- Imports `from datetime import UTC, datetime`.
- Stores the result of calling `FileEvidenceStore(tmp_path / 'evidence')` in `store`.
- Stores the result of calling `datetime(2026, 10, 27, tzinfo=UTC)` in `now`.
- Calls `store.write('a.txt', 'hello\n', 'P1', now)`.
- Checks that `store.read_all()` equals `{'a.txt': 'hello\n', 'manifest.json': store.read_…`; if not, the test fails.
- Stores `store.manifest()['a.txt']` in `entry`.
- Checks that `(entry.requirement, entry.produced_at, len(entry.…` equals `('P1', now, 64)`; if not, the test fails.
- Checks that `FileEvidenceStore(tmp_path / 'none').read_all()` equals `{}`; if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(ValueError, match='directly in')`:
  - Calls `store.write('../x', 'x', 'P1', now)`.

`tests/unit/infrastructure/test_adapters.py` lines 126 to 142:

```python
def test_the_catalogs_load_and_reject_bad_files(tmp_path):
    assert len(load_inventory(REPOSITORY_ROOT / "scope" / "before.toml").systems) == 10
    requirements, gaps = load_requirements(REPOSITORY_ROOT / "controls" / "requirements.toml")
    assert [r.id for r in requirements] == ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    assert gaps[0].requirement == "P7"
    assert gaps[0].due is not None
    bad = tmp_path / "bad.toml"
    bad.write_text(
        'title = "x"\n[[system]]\nid = "a"\nname = "A"\nteam = "t"\n[[edge]]\nfrom = "a"\nto = "ghost"\nkind = "data"\n'
    )
    with pytest.raises(CatalogError, match="bad edge"):
        load_inventory(bad)
    bad.write_text("[[system]]\nid = 'a'\n")
    with pytest.raises(CatalogError, match="missing"):
        load_inventory(bad)
    with pytest.raises(CatalogError):
        load_requirements(tmp_path / "nothing.toml")
```

**Test `test_the_catalogs_load_and_reject_bad_files`** checks: the catalogs load and reject bad files.

It takes: `tmp_path`.

Step by step:

- Checks that `len(load_inventory(REPOSITORY_ROOT / 'scope' / 'b…` equals `10`; if not, the test fails.
- Unpacks the result of calling `load_requirements(REPOSITORY_ROOT / 'controls' / 'requirements.toml')` into `(requirements, gaps)`.
- Checks that `[r.id for r in requirements]` equals `['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']`; if not, the test fails.
- Checks that `gaps[0].requirement` equals `'P7'`; if not, the test fails.
- Checks that `gaps[0].due` is not the same object as `None`; if not, the test fails.
- Stores `tmp_path / 'bad.toml'` in `bad`.
- Calls `bad.write_text('title = "x"\n[[system]]\nid = "a"\nname = "A"\nteam = "t"\n[[edge]]\nfrom = "a"\nto = "ghost"…`.
- Expects the steps inside to raise the error in `pytest.raises(CatalogError, match='bad edge')`:
  - Calls `load_inventory(bad)`.
- Calls `bad.write_text("[[system]]\nid = 'a'\n")`.
- Expects the steps inside to raise the error in `pytest.raises(CatalogError, match='missing')`:
  - Calls `load_inventory(bad)`.
- Expects the steps inside to raise the error in `pytest.raises(CatalogError)`:
  - Calls `load_requirements(tmp_path / 'nothing.toml')`.

`tests/unit/infrastructure/test_adapters.py` lines 145 to 154:

```python
def test_the_json_formatter_keeps_only_whitelisted_fields():
    import logging

    record = logging.LogRecord("merchant", logging.INFO, "f", 1, "payment %s", ("pi_x",), None)
    record.status = 200
    record.card_number = "never"
    document = json.loads(JsonFormatter().format(record))
    assert document["message"] == "payment pi_x"
    assert document["status"] == 200
    assert "card_number" not in document
```

**Test `test_the_json_formatter_keeps_only_whitelisted_fields`** checks: the json formatter keeps only whitelisted fields.

Step by step:

- Imports `import logging`.
- Stores the result of calling `logging.LogRecord('merchant', logging.INFO, 'f', 1, 'payment %s', ('pi_x',), None)` in `record`.
- Stores the number `200` in `record.status`.
- Stores the text `'never'` in `record.card_number`.
- Stores the result of calling `json.loads(JsonFormatter().format(record))` in `document`.
- Checks that `document['message']` equals `'payment pi_x'`; if not, the test fails.
- Checks that `document['status']` equals `200`; if not, the test fails.
- Checks that `'card_number'` is not in `document`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 157 to 163:

```python
@pytest.fixture
def provider():
    state = ProviderState(
        "sk_test_abc", "pk_test_abc", "w" * 32, "http://127.0.0.1:1/webhook", deliver=lambda url, body, sig: None
    )
    with LocalServer(create_provider_app(state), free_port()) as server:
        yield server.url, state
```

> **In plain words.** A **fixture** is a helper function marked `@pytest.fixture`. A test that names it as a parameter receives its return value, prepared fresh for that test.
> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** `yield` makes a function a **generator**: calling it returns an iterator that hands out one value at a time and remembers where it stopped.

**Function `provider`.**

Decorators: `@pytest.fixture`.

Step by step:

- Stores the result of calling `ProviderState('sk_test_abc', 'pk_test_abc', 'w' * 32, 'http://127.0.0.1:1/webhook', deliv…` in `state`.
- Inside a `with` block that opens `LocalServer(create_provider_app(state), free_port())` (named `server`):
  - Hands out the tuple `(server.url, state)` to the caller (`yield`).

`tests/unit/infrastructure/test_adapters.py` lines 166 to 177:

```python
def test_the_http_provider_creates_charges_and_refunds_against_the_stand_in(provider):
    url, state = provider
    client = HttpProvider(url, "sk_test_abc")
    customer = client.create_customer()
    intent = client.create_intent(1900, "eur", customer, save_card=True)
    assert (intent.status, intent.amount_cents, intent.customer_id) == ("requires_payment_method", 1900, customer)
    assert intent.client_secret.startswith(intent.id + "_secret_")
    assert client.retrieve_intent(intent.id).id == intent.id
    state.methods["pm_" + "a" * 24] = {"brand": "visa", "last4": "4242", "decline": False}
    again = client.charge_saved(customer, "pm_" + "a" * 24, 1900, "eur")
    assert again.status == "succeeded"
    assert client.refund(again.id).startswith("re_")
```

**Test `test_the_http_provider_creates_charges_and_refunds_against_the_stand_in`** checks: the http provider creates charges and refunds against the stand in.

It takes: `provider`.

Step by step:

- Unpacks `provider` into `(url, state)`.
- Stores the result of calling `HttpProvider(url, 'sk_test_abc')` in `client`.
- Stores the result of calling `client.create_customer()` in `customer`.
- Stores the result of calling `client.create_intent(1900, 'eur', customer, save_card=True)` in `intent`.
- Checks that `(intent.status, intent.amount_cents, intent.custo…` equals `('requires_payment_method', 1900, customer)`; if not, the test fails.
- Checks that `intent.client_secret.startswith(intent.id + '_secret_')`; if not, the test fails.
- Checks that `client.retrieve_intent(intent.id).id` equals `intent.id`; if not, the test fails.
- Stores the dictionary `{'brand': 'visa', 'last4': '4242', 'decline': False}` in `state.methods['pm_' + 'a' * 24]`.
- Stores the result of calling `client.charge_saved(customer, 'pm_' + 'a' * 24, 1900, 'eur')` in `again`.
- Checks that `again.status` equals `'succeeded'`; if not, the test fails.
- Checks that `client.refund(again.id).startswith('re_')`; if not, the test fails.

`tests/unit/infrastructure/test_adapters.py` lines 180 to 187:

```python
def test_a_4xx_is_the_providers_message_and_a_wrong_key_is_refused(provider):
    url, _ = provider
    with pytest.raises(PaymentError, match="Invalid secret key"):
        HttpProvider(url, "sk_test_wrong").create_customer()
    with pytest.raises(PaymentError, match="No such payment_intent"):
        HttpProvider(url, "sk_test_abc").retrieve_intent("pi_" + "0" * 24)
    with pytest.raises(PaymentError, match="only a succeeded payment"):
        HttpProvider(url, "sk_test_abc").refund("pi_" + "0" * 24)
```

**Test `test_a_4xx_is_the_providers_message_and_a_wrong_key_is_refused`** checks: a 4xx is the providers message and a wrong key is refused.

It takes: `provider`.

Step by step:

- Unpacks `provider` into `(url, _)`.
- Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='Invalid secret key')`:
  - Calls `HttpProvider(url, 'sk_test_wrong').create_customer()`.
- Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='No such payment_intent')`:
  - Calls `HttpProvider(url, 'sk_test_abc').retrieve_intent('pi_' + '0' * 24)`.
- Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='only a succeeded payment')`:
  - Calls `HttpProvider(url, 'sk_test_abc').refund('pi_' + '0' * 24)`.

`tests/unit/infrastructure/test_adapters.py` lines 190 to 215:

```python
def test_a_server_that_fails_is_retried_then_reported_and_an_unreachable_one_too():
    hits: list[int] = []

    class Failing(BaseHTTPRequestHandler):
        def do_POST(self):
            hits.append(1)
            self.send_response(503)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Failing)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    sleeps: list[float] = []
    try:
        with pytest.raises(PaymentError, match="failing"):
            HttpProvider(f"http://127.0.0.1:{server.server_port}", "sk_test_abc", sleep=sleeps.append).create_customer()
    finally:
        server.shutdown()
        server.server_close()
    assert len(hits) == 3
    assert sleeps == [0.2, 0.4]
    with pytest.raises(PaymentError, match="unreachable"):
        HttpProvider("http://127.0.0.1:1", "sk_test_abc", timeout=1, sleep=lambda s: None).create_customer()
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Test `test_a_server_that_fails_is_retried_then_reported_and_an_unreachable_one_too`** checks: a server that fails is retried then reported and an unreachable one too.

Step by step:

- Declares `hits` as a `list[int]` and stores the list `[]` in it.
- Defines a class `Failing`.
- Stores the result of calling `HTTPServer(('127.0.0.1', 0), Failing)` in `server`.
- Stores the result of calling `threading.Thread(target=server.serve_forever, daemon=True)` in `thread`.
- Calls `thread.start()`.
- Declares `sleeps` as a `list[float]` and stores the list `[]` in it.
- Tries:
  - Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='failing')`:
    - Calls `HttpProvider(f'http://127.0.0.1:{server.server_port}', 'sk_test_abc', sleep=sleeps.append).create_customer()`.
- Always, at the end:
  - Calls `server.shutdown()`.
  - Calls `server.server_close()`.
- Checks that `len(hits)` equals `3`; if not, the test fails.
- Checks that `sleeps` equals `[0.2, 0.4]`; if not, the test fails.
- Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='unreachable')`:
  - Calls `HttpProvider('http://127.0.0.1:1', 'sk_test_abc', timeout=1, sleep=lambda s: None).create_customer()`.

`tests/unit/infrastructure/test_adapters.py` lines 218 to 226:

```python
def test_a_local_server_stops_when_the_context_exits():
    from flask import Flask

    app = Flask(__name__)
    port = free_port()
    with LocalServer(app, port) as server:
        assert server.url == f"http://127.0.0.1:{port}"
    with closing(socket.socket()) as probe:
        assert probe.connect_ex(("127.0.0.1", port)) != 0
```

**Test `test_a_local_server_stops_when_the_context_exits`** checks: a local server stops when the context exits.

Step by step:

- Imports `from flask import Flask`.
- Stores the result of calling `Flask(__name__)` in `app`.
- Stores the result of calling `free_port()` in `port`.
- Inside a `with` block that opens `LocalServer(app, port)` (named `server`):
  - Checks that `server.url` equals `f'http://127.0.0.1:{port}'`; if not, the test fails.
- Inside a `with` block that opens `closing(socket.socket())` (named `probe`):
  - Checks that `probe.connect_ex(('127.0.0.1', port))` is different from `0`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/unit/infrastructure
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check tests/unit/infrastructure/test_adapters.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_settings_strip_trailing_slashes_and_apply_defaults` check?
   **Answer:** it checks: settings strip trailing slashes and apply defaults.
2. What does the test `test_live_keys_and_missing_values_are_refused` check?
   **Answer:** it checks: live keys and missing values are refused.
3. What does the test `test_the_order_table_holds_tokens_and_refuses_a_card_number` check?
   **Answer:** it checks: the order table holds tokens and refuses a card number.
4. What does the test `test_the_order_table_reports_its_columns_rows_and_dump` check?
   **Answer:** it checks: the order table reports its columns rows and dump.
5. What does the test `test_the_merchant_artifacts_cover_logs_backups_and_the_database_dump_but_skip_named_folders` check?
   **Answer:** it checks: the merchant artifacts cover logs backups and the database dump but skip named folders.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
