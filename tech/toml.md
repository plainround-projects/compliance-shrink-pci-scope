# TOML

## What it is

TOML (Tom's Obvious, Minimal Language) is a text format for settings. It has `key = value` pairs, `[tables]`
(named groups), lists in square brackets and comments after `#`. Python's own packaging tools and most Python
tools read it.

## Why this repository uses it

`pyproject.toml` is where Python projects state their name, dependencies and tool settings, in TOML. This
repository keeps all tool settings there (ruff, mypy, pytest, coverage, import-linter), so there is one file to read.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` | Project metadata and the settings of every tool. |

## How it works underneath

A TOML reader turns the text into nested dictionaries. `[tool.ruff]` becomes the key `tool` holding the key `ruff`.
`[[tool.mypy.overrides]]` (double brackets) adds one more item to a **list of tables**. Values have types: text in
double quotes, integers, floats, booleans (`true`/`false`) and lists. Tools read only their own `tool.NAME` table and
ignore the rest.

## Walkthrough of this repository's use

`pyproject.toml`:

```toml
[project]
name = "compliance-shrink-pci-scope"
version = "0.1.0"
description = "A checkout rebuilt so card data never reaches the merchant: a local payment provider with hosted fields, a scope calculator, a card-number scanner, a traffic capture and the evidence pack."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Sumit Srivastava" }]
dependencies = ["flask>=3.1,<4", "gunicorn>=23"]

[project.optional-dependencies]
dev = [
```

- `[project]` is a table. Each line inside is a key and a value.
- `dependencies = []` is an empty list.
- `license = { text = "MIT" }` is an **inline table**: a small table on one line.
- `authors = [{ name = "Sumit Srivastava" }]` is a list holding one inline table.

`pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8,<10",
    "pytest-cov>=5",
    "ruff>=0.6",
    "mypy>=1.11",
    "import-linter>=2.0",
    "pip-audit>=2.7",
]
```

A list can span lines. Each string is a requirement with a version range: `pytest>=8,<10` means "at least 8 and
below 10". The group name `dev` is what `uv pip compile --extra dev` used (see `hash-pinned-lock-files.md`).

`pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["src", "tests"]
```

`[tool.mypy]` is for mypy only. `files = ["src", "tests"]` is a list of strings.

Other tables in the same file are covered in the notes for each tool: `setuptools.md`, `pytest.md`, `pytest-cov.md`,
`ruff.md`, `mypy.md` and `import-linter.md`.


### The other TOML files

`scope/before.toml`:

```toml
title = "Before: the card number reaches the merchant's server"

[[system]]
id = "browser"
name = "Customer browser"
team = "customer"
touches_card = true
external = true

[[system]]
id = "web"
name = "Web server (naive.py)"
team = "developers"
touches_card = true

[[system]]
```

`title = ...` is a plain key. Each `[[system]]` (double brackets) adds one table to a list named `system`: an `id`, a `name`, the
`team` that runs it and flags such as `touches_card = true` or `external = true`. `edge` tables (later in the file) describe the links
between systems with `from`, `to` and `kind`. `controls/requirements.toml` uses `[[requirement]]` with nested `[[requirement.evidence]]`
and `[[gap]]`. See `tomllib.md`.

### The complete file `controls/requirements.toml`, line by line

`controls/requirements.toml` lines 1 to 3:

```toml
# What the redesign must show for a reduced-scope assessment, and the evidence for each. `pci-scope verify` fails when a
# requirement has no evidence and no tracked gap, a file is missing, empty, edited by hand, or does not say what the
# requirement needs. Requirement ids are this repository's own; they are not PCI DSS requirement numbers.
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- These lines are comments written by the author; they are quoted above.

`controls/requirements.toml` lines 5 to 7:

```toml
[[requirement]]
id = "P1"
text = "Card data never reaches the merchant: the card fields go from the browser to the provider only."
```

- `[[requirement]]` starts a new item in the list of tables named `requirement`.
- `id` is set to the text `"P1"`: the identifier.
- `text` is set to the text `"Card data never reaches the merchant: the card fields go from the br…`: the wording.

`controls/requirements.toml` lines 9 to 12:

```toml
  [[requirement.evidence]]
  file = "payment.har"
  kind = "har"
  proves = "the captured browser traffic: no request to the merchant carries a card field or number, and the card fields went to the provider"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"payment.har"`: the file.
- `kind` is set to the text `"har"`: the kind.
- `proves` is set to the text `"the captured browser traffic: no request to the merchant carries a c…`: what it proves.

`controls/requirements.toml` lines 14 to 17:

```toml
  [[requirement.evidence]]
  file = "payment-summary.txt"
  kind = "har_summary"
  proves = "the same capture, one line per request with where it went"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"payment-summary.txt"`: the file.
- `kind` is set to the text `"har_summary"`: the kind.
- `proves` is set to the text `"the same capture, one line per request with where it went"`: what it proves.

`controls/requirements.toml` lines 19 to 22:

```toml
  [[requirement.evidence]]
  file = "proof-after.txt"
  kind = "scan_after"
  proves = "a scan of the merchant's log, database and backups for card numbers and card fields, and the lesson's grep commands, all empty"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"proof-after.txt"`: the file.
- `kind` is set to the text `"scan_after"`: the kind.
- `proves` is set to the text `"a scan of the merchant's log, database and backups for card numbers …`: what it proves.

`controls/requirements.toml` lines 24 to 26:

```toml
[[requirement]]
id = "P2"
text = "The old route that accepted card details is gone."
```

- `[[requirement]]` starts a new item in the list of tables named `requirement`.
- `id` is set to the text `"P2"`: the identifier.
- `text` is set to the text `"The old route that accepted card details is gone."`: the wording.

`controls/requirements.toml` lines 28 to 31:

```toml
  [[requirement.evidence]]
  file = "route-check.txt"
  kind = "routes"
  proves = "POST and GET /pay on the merchant answer 404"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"route-check.txt"`: the file.
- `kind` is set to the text `"routes"`: the kind.
- `proves` is set to the text `"POST and GET /pay on the merchant answer 404"`: what it proves.

`controls/requirements.toml` lines 33 to 35:

```toml
[[requirement]]
id = "P3"
text = "The scope before and after is drawn, and the reduction is stated."
```

- `[[requirement]]` starts a new item in the list of tables named `requirement`.
- `id` is set to the text `"P3"`: the identifier.
- `text` is set to the text `"The scope before and after is drawn, and the reduction is stated."`: the wording.

`controls/requirements.toml` lines 37 to 40:

```toml
  [[requirement.evidence]]
  file = "scope-before.md"
  kind = "scope"
  proves = "the cardholder data environment of the naive checkout: 9 systems and 3 teams"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"scope-before.md"`: the file.
- `kind` is set to the text `"scope"`: the kind.
- `proves` is set to the text `"the cardholder data environment of the naive checkout: 9 systems and…`: what it proves.

`controls/requirements.toml` lines 42 to 45:

```toml
  [[requirement.evidence]]
  file = "scope-after.md"
  kind = "scope"
  proves = "the cardholder data environment after the redesign"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"scope-after.md"`: the file.
- `kind` is set to the text `"scope"`: the kind.
- `proves` is set to the text `"the cardholder data environment after the redesign"`: what it proves.

`controls/requirements.toml` lines 47 to 50:

```toml
  [[requirement.evidence]]
  file = "scope-change.md"
  kind = "scope_change"
  proves = "what left scope and what stays"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"scope-change.md"`: the file.
- `kind` is set to the text `"scope_change"`: the kind.
- `proves` is set to the text `"what left scope and what stays"`: what it proves.

`controls/requirements.toml` lines 52 to 54:

```toml
[[requirement]]
id = "P4"
text = "The problem was real: the naive checkout puts the card number in its log."
```

- `[[requirement]]` starts a new item in the list of tables named `requirement`.
- `id` is set to the text `"P4"`: the identifier.
- `text` is set to the text `"The problem was real: the naive checkout puts the card number in its…`: the wording.

`controls/requirements.toml` lines 56 to 59:

```toml
  [[requirement.evidence]]
  file = "proof-before.txt"
  kind = "scan_before"
  proves = "the same scan, run on the naive checkout after one test payment, finds the number"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"proof-before.txt"`: the file.
- `kind` is set to the text `"scan_before"`: the kind.
- `proves` is set to the text `"the same scan, run on the naive checkout after one test payment, fin…`: what it proves.

`controls/requirements.toml` lines 61 to 63:

```toml
[[requirement]]
id = "P5"
text = "Only tokens are stored."
```

- `[[requirement]]` starts a new item in the list of tables named `requirement`.
- `id` is set to the text `"P5"`: the identifier.
- `text` is set to the text `"Only tokens are stored."`: the wording.

`controls/requirements.toml` lines 65 to 68:

```toml
  [[requirement.evidence]]
  file = "token-storage.txt"
  kind = "tokens"
  proves = "the order table's columns, sample rows holding only pi_, cus_ and pm_ tokens, and the check for card-number columns"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"token-storage.txt"`: the file.
- `kind` is set to the text `"tokens"`: the kind.
- `proves` is set to the text `"the order table's columns, sample rows holding only pi_, cus_ and pm…`: what it proves.

`controls/requirements.toml` lines 70 to 72:

```toml
[[requirement]]
id = "P6"
text = "The payment page stays controlled, and what is still ours is written down."
```

- `[[requirement]]` starts a new item in the list of tables named `requirement`.
- `id` is set to the text `"P6"`: the identifier.
- `text` is set to the text `"The payment page stays controlled, and what is still ours is written…`: the wording.

`controls/requirements.toml` lines 74 to 77:

```toml
  [[requirement.evidence]]
  file = "checkout-page-controls.txt"
  kind = "headers"
  proves = "the content security policy of the payment page and the inventory of the scripts and frames it loads"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"checkout-page-controls.txt"`: the file.
- `kind` is set to the text `"headers"`: the kind.
- `proves` is set to the text `"the content security policy of the payment page and the inventory of…`: what it proves.

`controls/requirements.toml` lines 79 to 82:

```toml
  [[requirement.evidence]]
  file = "responsibilities.md"
  kind = "responsibilities"
  proves = "what is now the provider's and what is still the merchant's"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"responsibilities.md"`: the file.
- `kind` is set to the text `"responsibilities"`: the kind.
- `proves` is set to the text `"what is now the provider's and what is still the merchant's"`: what it proves.

`controls/requirements.toml` lines 84 to 86:

```toml
[[requirement]]
id = "P7"
text = "The provider is itself compliant, shown by its attestation of compliance."
```

- `[[requirement]]` starts a new item in the list of tables named `requirement`.
- `id` is set to the text `"P7"`: the identifier.
- `text` is set to the text `"The provider is itself compliant, shown by its attestation of compli…`: the wording.

`controls/requirements.toml` lines 88 to 91:

```toml
  [[requirement.evidence]]
  file = "provider-attestation.md"
  kind = "attestation"
  proves = "the record of the provider's attestation of compliance, its date and the services it covers"
```

- `[[requirement.evidence]]` starts a new item in the list of tables named `requirement.evidence`.
- `file` is set to the text `"provider-attestation.md"`: the file.
- `kind` is set to the text `"attestation"`: the kind.
- `proves` is set to the text `"the record of the provider's attestation of compliance, its date and…`: what it proves.

`controls/requirements.toml` lines 93 to 97:

```toml
[[gap]]
requirement = "P7"
reason = "This build uses a local stand-in for the provider, which has no attestation. With a real provider, download its attestation of compliance, record its date and services here, and close this gap."
ticket = "PCI-1"
due = 2026-12-01
```

- `[[gap]]` starts a new item in the list of tables named `gap`.
- `requirement` is set to the text `"P7"`: the requirement id.
- `reason` is set to the text `"This build uses a local stand-in for the provider, which has no atte…`: why.
- `ticket` is set to the text `"PCI-1"`: the ticket.
- `due` is set to the date `2026-12-01`: the due date.

### The complete file `pyproject.toml`, line by line

`pyproject.toml` lines 1 to 3:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- `[build-system]` starts the table `build-system`; the lines below belong to it.
- `requires` is set to a list `["setuptools>=75"]`: what must be installed first (for a control: what it demands).
- `build-backend` is set to the text `"setuptools.build_meta"`: the program that builds the project.

`pyproject.toml` lines 5 to 13:

```toml
[project]
name = "compliance-shrink-pci-scope"
version = "0.1.0"
description = "A checkout rebuilt so card data never reaches the merchant: a local payment provider with hosted fields, a scope calculator, a card-number scanner, a traffic capture and the evidence pack."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Sumit Srivastava" }]
dependencies = ["flask>=3.1,<4", "gunicorn>=23"]
```

- `[project]` starts the table `project`; the lines below belong to it.
- `name` is set to the text `"compliance-shrink-pci-scope"`: the project's or item's name.
- `version` is set to the text `"0.1.0"`: the version number.
- `description` is set to the text `"A checkout rebuilt so card data never reaches the merchant: a local …`: a description.
- `readme` is set to the text `"README.md"`: the file used as the long description.
- `requires-python` is set to the text `">=3.12"`: the oldest Python version allowed.
- `license` is set to a small table `{ text = "MIT" }`: the license.
- `authors` is set to a list `[{ name = "Sumit Srivastava" }]`: the authors.
- `dependencies` is set to a list `["flask>=3.1,<4", "gunicorn>=23"]`: the packages needed to run.

`pyproject.toml` lines 15 to 23:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8,<10",
    "pytest-cov>=5",
    "ruff>=0.6",
    "mypy>=1.11",
    "import-linter>=2.0",
    "pip-audit>=2.7",
]
```

- `[project.optional-dependencies]` starts the table `project.optional-dependencies`; the lines below belong to it.
- `dev` is set to a list `[ "pytest>=8,<10", "pytest-cov>=5", "ruff>=0.6", "mypy>=1.11", "import-linter>=…`.

`pyproject.toml` lines 25 to 26:

```toml
[project.scripts]
pci-scope = "pci_scope.interfaces.cli:main"
```

- `[project.scripts]` starts the table `project.scripts`; the lines below belong to it.
- `pci-scope` is set to the text `"pci_scope.interfaces.cli:main"`.

`pyproject.toml` lines 28 to 29:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

- `[tool.setuptools.packages.find]` starts the table `tool.setuptools.packages.find`; the lines below belong to it.
- `where` is set to a list `["src"]`: the folder to search for packages.

`pyproject.toml` lines 31 to 35:

```toml
[tool.ruff]
line-length = 120
target-version = "py312"
src = ["src", "tests"]
extend-exclude = ["tech"]  # tech/ quotes fragments of code inside Markdown; ruff 0.17 would try to format them
```

- `[tool.ruff]` starts the table `tool.ruff`; the lines below belong to it.
- `line-length` is set to the number `120`: the longest allowed line, in characters.
- `target-version` is set to the text `"py312"`: the Python version to write for.
- `src` is set to a list `["src", "tests"]`: where first-party code lives.
- `extend-exclude` is set to a list `["tech"]`: extra folders the tool skips.

`pyproject.toml` lines 37 to 38:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "N", "C4", "RUF", "PT", "D100", "D101", "D103", "D104"]
```

- `[tool.ruff.lint]` starts the table `tool.ruff.lint`; the lines below belong to it.
- `select` is set to a list `["E", "F", "I", "B", "UP", "SIM", "N", "C4", "RUF", "PT", "D100", "D101", "D103…`: the rule groups switched on.

`pyproject.toml` lines 40 to 41:

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D"]
```

- `[tool.ruff.lint.per-file-ignores]` starts the table `tool.ruff.lint.per-file-ignores`; the lines below belong to it.
- `"tests/**"` is set to a list `["D"]`.

`pyproject.toml` lines 43 to 46:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["src", "tests"]
```

- `[tool.mypy]` starts the table `tool.mypy`; the lines below belong to it.
- `python_version` is set to the text `"3.12"`: the Python version to check as.
- `strict` is set to `true`: switch on all the strict checks.
- `files` is set to a list `["src", "tests"]`: the files or folders to check.

`pyproject.toml` lines 48 to 52:

```toml
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false
```

- `[[tool.mypy.overrides]]` starts a new item in the list of tables named `tool.mypy.overrides`.
- `module` is set to a list `["tests.*"]`.
- `disallow_untyped_defs` is set to `false`.
- `disallow_incomplete_defs` is set to `false`.
- `disallow_untyped_calls` is set to `false`.

`pyproject.toml` lines 54 to 57:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
markers = ["e2e: runs the lesson's scenario against real local servers (provider, merchant, naive)"]
```

- `[tool.pytest.ini_options]` starts the table `tool.pytest.ini_options`; the lines below belong to it.
- `testpaths` is set to a list `["tests"]`: where to look for tests.
- `addopts` is set to the text `"-ra --strict-markers"`: options always added to a run.
- `markers` is set to a list `["e2e: runs the lesson's scenario against real local servers (provider, merchan…`: the registered test markers.

`pyproject.toml` lines 59 to 61:

```toml
[tool.coverage.run]
source = ["pci_scope"]
branch = true
```

- `[tool.coverage.run]` starts the table `tool.coverage.run`; the lines below belong to it.
- `source` is set to a list `["pci_scope"]`: the package to measure.
- `branch` is set to `true`: also measure each branch of an if.

`pyproject.toml` lines 63 to 65:

```toml
[tool.coverage.report]
show_missing = true
skip_covered = false
```

- `[tool.coverage.report]` starts the table `tool.coverage.report`; the lines below belong to it.
- `show_missing` is set to `true`: list the missed line numbers.
- `skip_covered` is set to `false`: leave fully covered files out of the table.

`pyproject.toml` lines 67 to 69:

```toml
[tool.importlinter]
root_package = "pci_scope"
include_external_packages = true
```

- `[tool.importlinter]` starts the table `tool.importlinter`; the lines below belong to it.
- `root_package` is set to the text `"pci_scope"`: the package to analyse.
- `include_external_packages` is set to `true`: let contracts name installed packages.

`pyproject.toml` lines 71 to 79:

```toml
[[tool.importlinter.contracts]]
name = "Layers: interfaces -> infrastructure -> application -> domain, never upward"
type = "layers"
layers = [
    "pci_scope.interfaces",
    "pci_scope.infrastructure",
    "pci_scope.application",
    "pci_scope.domain",
]
```

- `[[tool.importlinter.contracts]]` starts a new item in the list of tables named `tool.importlinter.contracts`.
- `name` is set to the text `"Layers: interfaces -> infrastructure -> application -> domain, never…`: the project's or item's name.
- `type` is set to the text `"layers"`: the kind of contract.
- `layers` is set to a list `[ "pci_scope.interfaces", "pci_scope.infrastructure", "pci_scope.application", …`: the modules from highest to lowest.

`pyproject.toml` lines 81 to 85:

```toml
[[tool.importlinter.contracts]]
name = "Domain and application know nothing about Flask or SQLite"
type = "forbidden"
source_modules = ["pci_scope.domain", "pci_scope.application"]
forbidden_modules = ["pci_scope.infrastructure", "pci_scope.interfaces", "flask", "sqlite3"]
```

- `[[tool.importlinter.contracts]]` starts a new item in the list of tables named `tool.importlinter.contracts`.
- `name` is set to the text `"Domain and application know nothing about Flask or SQLite"`: the project's or item's name.
- `type` is set to the text `"forbidden"`: the kind of contract.
- `source_modules` is set to a list `["pci_scope.domain", "pci_scope.application"]`: the modules the rule applies to.
- `forbidden_modules` is set to a list `["pci_scope.infrastructure", "pci_scope.interfaces", "flask", "sqlite3"]`: the modules they must not import.

### The complete file `scope/after.toml`, line by line

`scope/after.toml` lines 1 to 1:

```toml
title = "After: the card number goes from the browser to the provider"
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- `title` is set to the text `"After: the card number goes from the browser to the provider"`: the title.

`scope/after.toml` lines 3 to 8:

```toml
[[system]]
id = "browser"
name = "Customer browser"
team = "customer"
touches_card = true
external = true
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"browser"`: the identifier.
- `name` is set to the text `"Customer browser"`: the project's or item's name.
- `team` is set to the text `"customer"`: the team that runs it.
- `touches_card` is set to `true`: card data reaches it directly.
- `external` is set to `true`: outside the merchant's control.

`scope/after.toml` lines 10 to 14:

```toml
[[system]]
id = "provider"
name = "Payment provider (hosted fields)"
team = "provider"
external = true
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"provider"`: the identifier.
- `name` is set to the text `"Payment provider (hosted fields)"`: the project's or item's name.
- `team` is set to the text `"provider"`: the team that runs it.
- `external` is set to `true`: outside the merchant's control.

`scope/after.toml` lines 16 to 20:

```toml
[[system]]
id = "web"
name = "Web server (serves the checkout page)"
team = "developers"
serves_payment_page = true
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"web"`: the identifier.
- `name` is set to the text `"Web server (serves the checkout page)"`: the project's or item's name.
- `team` is set to the text `"developers"`: the team that runs it.
- `serves_payment_page` is set to `true`: it serves the payment page.

`scope/after.toml` lines 22 to 25:

```toml
[[system]]
id = "log"
name = "Request log"
team = "operations"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"log"`: the identifier.
- `name` is set to the text `"Request log"`: the project's or item's name.
- `team` is set to the text `"operations"`: the team that runs it.

`scope/after.toml` lines 27 to 30:

```toml
[[system]]
id = "shipping"
name = "Log shipping"
team = "operations"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"shipping"`: the identifier.
- `name` is set to the text `"Log shipping"`: the project's or item's name.
- `team` is set to the text `"operations"`: the team that runs it.

`scope/after.toml` lines 32 to 35:

```toml
[[system]]
id = "search"
name = "Log search tool"
team = "support"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"search"`: the identifier.
- `name` is set to the text `"Log search tool"`: the project's or item's name.
- `team` is set to the text `"support"`: the team that runs it.

`scope/after.toml` lines 37 to 40:

```toml
[[system]]
id = "db"
name = "Order database"
team = "developers"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"db"`: the identifier.
- `name` is set to the text `"Order database"`: the project's or item's name.
- `team` is set to the text `"developers"`: the team that runs it.

`scope/after.toml` lines 42 to 45:

```toml
[[system]]
id = "bak"
name = "Backups"
team = "operations"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"bak"`: the identifier.
- `name` is set to the text `"Backups"`: the project's or item's name.
- `team` is set to the text `"operations"`: the team that runs it.

`scope/after.toml` lines 47 to 50:

```toml
[[system]]
id = "ci"
name = "CI/CD pipeline"
team = "developers"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"ci"`: the identifier.
- `name` is set to the text `"CI/CD pipeline"`: the project's or item's name.
- `team` is set to the text `"developers"`: the team that runs it.

`scope/after.toml` lines 52 to 55:

```toml
[[system]]
id = "admin"
name = "Admin accounts"
team = "operations"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"admin"`: the identifier.
- `name` is set to the text `"Admin accounts"`: the project's or item's name.
- `team` is set to the text `"operations"`: the team that runs it.

`scope/after.toml` lines 57 to 60:

```toml
[[system]]
id = "laptops"
name = "Developer laptops that read logs"
team = "developers"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"laptops"`: the identifier.
- `name` is set to the text `"Developer laptops that read logs"`: the project's or item's name.
- `team` is set to the text `"developers"`: the team that runs it.

`scope/after.toml` lines 62 to 65:

```toml
[[edge]]
from = "browser"
to = "provider"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"browser"`: where the link starts.
- `to` is set to the text `"provider"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/after.toml` lines 67 to 70:

```toml
[[edge]]
from = "web"
to = "log"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"web"`: where the link starts.
- `to` is set to the text `"log"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/after.toml` lines 72 to 75:

```toml
[[edge]]
from = "log"
to = "shipping"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"log"`: where the link starts.
- `to` is set to the text `"shipping"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/after.toml` lines 77 to 80:

```toml
[[edge]]
from = "shipping"
to = "search"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"shipping"`: where the link starts.
- `to` is set to the text `"search"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/after.toml` lines 82 to 85:

```toml
[[edge]]
from = "web"
to = "db"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"web"`: where the link starts.
- `to` is set to the text `"db"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/after.toml` lines 87 to 90:

```toml
[[edge]]
from = "db"
to = "bak"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"db"`: where the link starts.
- `to` is set to the text `"bak"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/after.toml` lines 92 to 95:

```toml
[[edge]]
from = "log"
to = "bak"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"log"`: where the link starts.
- `to` is set to the text `"bak"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/after.toml` lines 97 to 100:

```toml
[[edge]]
from = "search"
to = "laptops"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"search"`: where the link starts.
- `to` is set to the text `"laptops"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/after.toml` lines 102 to 105:

```toml
[[edge]]
from = "ci"
to = "web"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"ci"`: where the link starts.
- `to` is set to the text `"web"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/after.toml` lines 107 to 110:

```toml
[[edge]]
from = "admin"
to = "web"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"web"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/after.toml` lines 112 to 115:

```toml
[[edge]]
from = "admin"
to = "log"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"log"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/after.toml` lines 117 to 120:

```toml
[[edge]]
from = "admin"
to = "search"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"search"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/after.toml` lines 122 to 125:

```toml
[[edge]]
from = "admin"
to = "db"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"db"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/after.toml` lines 127 to 130:

```toml
[[edge]]
from = "admin"
to = "bak"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"bak"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

### The complete file `scope/before.toml`, line by line

`scope/before.toml` lines 1 to 1:

```toml
title = "Before: the card number reaches the merchant's server"
```

> **In plain words.** TOML is a settings format. `key = value` sets a value; `[table]` starts a named group of settings; `[[table]]` adds one more item to a list of such groups; text is in double quotes, lists in square brackets; `#` starts a comment.

- `title` is set to the text `"Before: the card number reaches the merchant's server"`: the title.

`scope/before.toml` lines 3 to 8:

```toml
[[system]]
id = "browser"
name = "Customer browser"
team = "customer"
touches_card = true
external = true
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"browser"`: the identifier.
- `name` is set to the text `"Customer browser"`: the project's or item's name.
- `team` is set to the text `"customer"`: the team that runs it.
- `touches_card` is set to `true`: card data reaches it directly.
- `external` is set to `true`: outside the merchant's control.

`scope/before.toml` lines 10 to 14:

```toml
[[system]]
id = "web"
name = "Web server (naive.py)"
team = "developers"
touches_card = true
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"web"`: the identifier.
- `name` is set to the text `"Web server (naive.py)"`: the project's or item's name.
- `team` is set to the text `"developers"`: the team that runs it.
- `touches_card` is set to `true`: card data reaches it directly.

`scope/before.toml` lines 16 to 19:

```toml
[[system]]
id = "log"
name = "Request log"
team = "operations"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"log"`: the identifier.
- `name` is set to the text `"Request log"`: the project's or item's name.
- `team` is set to the text `"operations"`: the team that runs it.

`scope/before.toml` lines 21 to 24:

```toml
[[system]]
id = "shipping"
name = "Log shipping"
team = "operations"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"shipping"`: the identifier.
- `name` is set to the text `"Log shipping"`: the project's or item's name.
- `team` is set to the text `"operations"`: the team that runs it.

`scope/before.toml` lines 26 to 29:

```toml
[[system]]
id = "search"
name = "Log search tool"
team = "support"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"search"`: the identifier.
- `name` is set to the text `"Log search tool"`: the project's or item's name.
- `team` is set to the text `"support"`: the team that runs it.

`scope/before.toml` lines 31 to 34:

```toml
[[system]]
id = "db"
name = "Order database"
team = "developers"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"db"`: the identifier.
- `name` is set to the text `"Order database"`: the project's or item's name.
- `team` is set to the text `"developers"`: the team that runs it.

`scope/before.toml` lines 36 to 39:

```toml
[[system]]
id = "bak"
name = "Backups"
team = "operations"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"bak"`: the identifier.
- `name` is set to the text `"Backups"`: the project's or item's name.
- `team` is set to the text `"operations"`: the team that runs it.

`scope/before.toml` lines 41 to 44:

```toml
[[system]]
id = "ci"
name = "CI/CD pipeline"
team = "developers"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"ci"`: the identifier.
- `name` is set to the text `"CI/CD pipeline"`: the project's or item's name.
- `team` is set to the text `"developers"`: the team that runs it.

`scope/before.toml` lines 46 to 49:

```toml
[[system]]
id = "admin"
name = "Admin accounts"
team = "operations"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"admin"`: the identifier.
- `name` is set to the text `"Admin accounts"`: the project's or item's name.
- `team` is set to the text `"operations"`: the team that runs it.

`scope/before.toml` lines 51 to 54:

```toml
[[system]]
id = "laptops"
name = "Developer laptops that read logs"
team = "developers"
```

- `[[system]]` starts a new item in the list of tables named `system`.
- `id` is set to the text `"laptops"`: the identifier.
- `name` is set to the text `"Developer laptops that read logs"`: the project's or item's name.
- `team` is set to the text `"developers"`: the team that runs it.

`scope/before.toml` lines 56 to 59:

```toml
[[edge]]
from = "browser"
to = "web"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"browser"`: where the link starts.
- `to` is set to the text `"web"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/before.toml` lines 61 to 64:

```toml
[[edge]]
from = "web"
to = "log"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"web"`: where the link starts.
- `to` is set to the text `"log"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/before.toml` lines 66 to 69:

```toml
[[edge]]
from = "log"
to = "shipping"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"log"`: where the link starts.
- `to` is set to the text `"shipping"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/before.toml` lines 71 to 74:

```toml
[[edge]]
from = "shipping"
to = "search"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"shipping"`: where the link starts.
- `to` is set to the text `"search"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/before.toml` lines 76 to 79:

```toml
[[edge]]
from = "web"
to = "db"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"web"`: where the link starts.
- `to` is set to the text `"db"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/before.toml` lines 81 to 84:

```toml
[[edge]]
from = "db"
to = "bak"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"db"`: where the link starts.
- `to` is set to the text `"bak"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/before.toml` lines 86 to 89:

```toml
[[edge]]
from = "log"
to = "bak"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"log"`: where the link starts.
- `to` is set to the text `"bak"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/before.toml` lines 91 to 94:

```toml
[[edge]]
from = "search"
to = "laptops"
kind = "data"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"search"`: where the link starts.
- `to` is set to the text `"laptops"`: where the link ends.
- `kind` is set to the text `"data"`: the kind.

`scope/before.toml` lines 96 to 99:

```toml
[[edge]]
from = "ci"
to = "web"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"ci"`: where the link starts.
- `to` is set to the text `"web"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/before.toml` lines 101 to 104:

```toml
[[edge]]
from = "admin"
to = "web"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"web"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/before.toml` lines 106 to 109:

```toml
[[edge]]
from = "admin"
to = "log"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"log"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/before.toml` lines 111 to 114:

```toml
[[edge]]
from = "admin"
to = "search"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"search"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/before.toml` lines 116 to 119:

```toml
[[edge]]
from = "admin"
to = "db"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"db"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

`scope/before.toml` lines 121 to 124:

```toml
[[edge]]
from = "admin"
to = "bak"
kind = "control"
```

- `[[edge]]` starts a new item in the list of tables named `edge`.
- `from` is set to the text `"admin"`: where the link starts.
- `to` is set to the text `"bak"`: where the link ends.
- `kind` is set to the text `"control"`: the kind.

## Try it yourself

```bash
.venv/bin/python -c "import tomllib, pprint; pprint.pprint(tomllib.load(open('pyproject.toml','rb'))['project'])"
```
Prints the `[project]` table as a Python dictionary (name, version, `requires-python`, ...).

```bash
.venv/bin/python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(list(d['tool']))"
```
Prints `['ruff', 'mypy', 'pytest', 'coverage', 'importlinter', 'setuptools']` (the tables under `tool`).

```bash
.venv/bin/python -c "import tomllib; print(tomllib.loads('a = [1, 2]\nb = {c = true}'))"
```
Prints `{'a': [1, 2], 'b': {'c': True}}`.


```bash
.venv/bin/python -c "import tomllib; d = tomllib.load(open('scope/before.toml','rb')); print(d['title'], '|', len(d['system']), 'systems,', len(d['edge']), 'edges')"
```
Prints the title and the counts of systems and edges.

## Mistakes people make

- **Quoting numbers** (`"120"`) so the value is text, not a number.
- **Mixing up `[table]` and `[[list of tables]]`.**
- **Forgetting commas** between list items.
- **Expecting comments to be kept** when a program rewrites the file.

## Check yourself

1. What does `[tool.ruff]` define?
   **Answer:** A table named `ruff` inside the table `tool`, holding ruff's settings.
2. What is the difference between `[x]` and `[[x]]`?
   **Answer:** `[x]` is one table; `[[x]]` adds an item to a list of tables.
3. How do you write a list?
   **Answer:** In square brackets, separated by commas.
4. Which Python module reads TOML?
   **Answer:** `tomllib`, in the standard library since 3.11.
5. What does `pytest>=8,<10` accept?
   **Answer:** Versions 8.x and 9.x.

## Further reading

- TOML 1.0.0 specification: <https://toml.io/en/v1.0.0>
- `pyproject.toml` specification: <https://packaging.python.org/en/latest/specifications/pyproject-toml/>
- Python `tomllib` (3.12): <https://docs.python.org/3.12/library/tomllib.html>
