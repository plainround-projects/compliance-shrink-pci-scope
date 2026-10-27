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
