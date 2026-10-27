# Make

## What it is

Make is a command-line tool from the 1970s. You describe **targets** (things you want) in a file called `Makefile`.
Each target lists what it needs first and the commands that produce it. You then type `make <target>` and Make runs
the commands. It also skips work that is already done, by comparing file dates.

People use it today less to compile programs and more as a short, standard name for project commands.

## Why this repository uses it

Every repository in this series answers three questions with the same three commands: `make run`, `make test`,
`make lint`. A reader who has never seen the project can type them without reading anything else. Make also keeps
the commands the same on a laptop and in CI.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` | Defines the targets listed in `make help`. |
| .github/workflows/ci.yml | Calls `make check`, `make audit`, `make test-e2e`, `make run` and `make verify`. |
| .editorconfig | Tells editors to use real tab characters in `Makefile`. |
| .env / .env.example | Make reads `.env` with `-include` and exports it. |
| README.md | Every command in the proof table is a `make` target. |

## How it works underneath

1. You run `make test`. Make reads `Makefile` from the current folder.
2. It finds the rule whose target is `test`. It looks at the prerequisites (`$(STAMP)`).
3. For each prerequisite it checks whether there is a rule to build it and whether the file is older than its own
   prerequisites. If so it builds it first. A prerequisite that is not a file (a `.PHONY` name) always runs.
4. It then runs the recipe. **Each recipe line runs in its own new shell** (`/bin/sh`, not your terminal). So a `cd`
   on one line does not affect the next line, and shell variables do not carry over.
5. If a line exits with a status other than 0, Make stops and reports `Error 1` (or similar). Success is status 0.

Make expands `$(NAME)` itself before the shell sees the line. A single `$` in front of a shell variable would have to
be written `$$`; this Makefile does not need that.

## Walkthrough of this repository's use

Make reads the file `Makefile`. A Makefile is a list of **rules**. A rule has a target (a name), optional
prerequisites (what must be ready first) and a recipe (the shell commands that build the target). The recipe lines
start with a tab, not spaces. That is why `.editorconfig` sets `indent_style = tab` for this file.

### The variables at the top

`Makefile`:

```make
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
CLI := $(VENV)/bin/pci-scope
```

- `# make up | run | ...` on the first line is only a comment (a line that starts with `#`).
- `PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)` sets `PYTHON` only if it
  is not already set (`?=`). `$(shell ...)` runs a shell command and uses its output. `command -v NAME` prints the
  path of a program if it exists and prints nothing (and fails) if it does not. The `||` means "if the left side
  failed, try the right side". So the line picks Python 3.13, else 3.12, else any `python3`.
- `VENV := .venv` uses `:=`, which evaluates the right side once, right now. `.venv` is the folder of the
  virtual environment (see `venv-and-pip.md`).
- `PY := $(VENV)/bin/python` and `CLI := $(VENV)/bin/pci-scope` build paths from earlier variables. `$(VENV)` means
  "the value of VENV". Using these paths means no one has to "activate" the environment.
- `STAMP := $(VENV)/.installed` names an empty marker file. Its date says when the install last finished.

`Makefile`:

```make
-include .env
export
```

- `-include .env` reads the file `.env` if it exists. The leading `-` means "do not fail if it is missing". The
  file holds lines like `EVIDENCE_DIR=.`, which Make reads as variable assignments.
- `export` with nothing after it makes every Make variable visible to the programs Make starts. That is how
  `pci-scope` sees `EVIDENCE_DIR` and the other settings without any extra code.

`Makefile`:

```make
.PHONY: help install env up db run verify scope scan queries serve-provider serve-merchant serve-naive docker-build test \
```

`.PHONY` lists targets that are **not files**. Without it, a file called `test` or `check` in the folder would make
Make think the target is already built and skip it.

### The targets

`Makefile`:

```make
help: ## list the targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

`help` prints every target with its `##` description. The pipeline is explained in `bash.md`. The `@` at the start of
the recipe line tells Make not to echo the command before running it.

`Makefile`:

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

This is the one rule that builds a real file. `$(STAMP): requirements-dev.lock pyproject.toml` says: the marker
`.venv/.installed` depends on the lock file and `pyproject.toml`. Make compares file dates. If either input is newer
than the marker, or the marker is missing, Make runs the recipe. Otherwise it skips it. That makes every other target
fast after the first time.
- Line 1 makes the virtual environment folder.
- Line 2 installs the exact, hash-checked packages from the lock file (`pip install --require-hashes`).
- Line 3 installs this project itself in editable mode without touching dependencies (`--no-deps -e .`).
- `touch $@` creates or refreshes the marker. `$@` is Make's automatic variable for "the target of this rule".

`Makefile`:

```make
install: $(STAMP) ## create .venv from the hash-pinned lock file
```

`install` is just a friendly name for the stamp: it has the stamp as a prerequisite and no recipe of its own.

`Makefile`:

```make
env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }
```

`env` copies `.env.example` to `.env` the first time, and does nothing afterwards. It has no `##`, so `make help`
hides it: it is a helper, not a command for people.

`Makefile`:

```make
up: env $(STAMP) ## prepare the environment (there are no services to start)
```

`up` means "get ready to run". Here that is the `.env` file and the virtual environment. The lesson template calls
the target `up` for every repository, even when there are no services to start.


`Makefile`:

```make
db: $(STAMP) ## create the merchant's order table with sql/001_schema.sql and the sample rows of sql/002_seed.sql
	$(CLI) db
```

`db` creates the merchant's SQLite database from `sql/` by calling the program (`pci-scope db`).

`Makefile`:

```make
run: up ## the lesson's scenario: naive checkout, redesign, proof, scope, evidence pack, verification
	$(CLI) demo
```

`run` first makes sure `up` is done, then runs the whole scenario with `pci-scope demo`: the naive checkout, the redesign, the proof, the scope, the evidence pack and its verification.
This is the command the README's "Done when" table points at.

`Makefile`:

```make
verify: $(STAMP) ## check that every requirement maps to evidence and every file says what it should
	$(CLI) verify

scope: $(STAMP) ## print the cardholder data environment before and after, and what changed
	$(CLI) scope
```

`verify` checks the evidence pack against the requirements; `scope` prints the cardholder data environment before and after; `scan` searches a folder for card
numbers (`make scan PATHS="state evidence"`: `$(PATHS)` is a Make variable you give on the command line); `queries` runs the SQL file with the `sqlite3` program.

`Makefile`:

```make
serve-provider: $(STAMP) ## run the local payment provider on its port
	$(CLI) serve provider

serve-merchant: $(STAMP) ## run the redesigned merchant on its port
	$(CLI) serve merchant

serve-naive: $(STAMP) ## run the naive checkout (to be measured, test card only)
	$(CLI) serve naive
```

Each `serve-*` target starts one app on its configured port. The naive one is "to be measured, test card only".

`Makefile`:

```make
test: $(STAMP) ## unit tests with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest tests/unit --cov=pci_scope --cov-report=term
	$(PY) -m coverage report --include='src/pci_scope/domain/*,src/pci_scope/application/*' --fail-under=95
```

`test` runs the unit tests under coverage and requires 95 percent in `domain/` and `application/`. `test-e2e` runs the end-to-end scenario selected by `-m e2e`.

`Makefile`:

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports
```

`lint` runs ruff, the format check, mypy and import-linter.


`Makefile`:

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

`Makefile`:

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

`Makefile`:

```make
check: lint test ## everything CI runs apart from the audit
```

`check: lint test` has no recipe. It only lists two prerequisites, so `make check` means "run `lint` and then `test`".
The CI file calls `make check` so that CI and a laptop run the same thing.

`Makefile`:

```make
down: ## remove generated output (nothing is running)
	rm -rf build
```

`Makefile`:

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage htmlcov
```

`down` deletes generated output. `clean` has `down` as a prerequisite and also deletes the virtual environment and
every cache folder. `rm -rf` removes a folder and everything in it without asking.

### The complete file `Makefile`, line by line

`Makefile` lines 1 to 6:

```make
# make up | run | test | lint | audit | check | down   (make help lists all)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
CLI := $(VENV)/bin/pci-scope
```

> **In plain words.** A Makefile is a list of **rules**. A rule has a target (a name), the things it needs first, and a recipe (shell commands, each line starting with a tab). `make name` runs the recipe after making sure the needs are ready. `$(NAME)` means "the value of the Make variable NAME"; `$@` means "this rule's target".

- Sets the Make variable `PYTHON` only if it is not already set to `$(shell command -v python3.13 || command -v python3.12 || command -v python3)`. The `$(shell ...)` part runs a shell command and uses its output.
- Sets the Make variable `VENV` once, right now to `.venv`.
- Sets the Make variable `PY` once, right now to `$(VENV)/bin/python`.
- Sets the Make variable `STAMP` once, right now to `$(VENV)/.installed`.
- Sets the Make variable `CLI` once, right now to `$(VENV)/bin/pci-scope`.

`Makefile` lines 8 to 9:

```make
-include .env
export
```

- `-include .env` reads that file if it exists; the leading `-` means "do not fail if it is missing". Its `NAME=value` lines become Make variables.
- `export` on its own passes every Make variable to the programs Make starts, so they see the settings from `.env`.

`Makefile` lines 11 to 12:

```make
.PHONY: help install env up db run verify scope scan queries serve-provider serve-merchant serve-naive docker-build test \
        test-e2e lint format audit check down clean
```

- `.PHONY` lists names that are commands, not files, so Make always runs them even if a file of that name exists.

`Makefile` lines 14 to 15:

```make
help: ## list the targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

- Defines the target `help`. It has no prerequisites. Its help text is "list the targets".
- Recipe line: runs grep, which searches text with `-hE` (hide file names, extended regex), `^[a-z-]+:.*##`, `$(MAKEFILE_LIST)`; then its output is passed to a command that runs sed, the stream editor with `-E` (extended regular expressions), `s/:.*## /\t/`; then its output is passed to a command that runs sort, which orders lines. (the leading `@` stops Make from printing the command first)

`Makefile` lines 17 to 21:

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

- Defines the target `$(STAMP)`. It needs `requirements-dev.lock pyproject.toml` to be ready first.
- Recipe line: runs `venv` with `$(VENV)` (run through Python with `-m`).
- Recipe line: runs pip, the package installer, subcommand `install` with `-q` (quiet: print less), `--require-hashes` (refuse any package without a pinned hash), `-r requirements-dev.lock` (read the list from the named file).
- Recipe line: runs pip, the package installer, subcommand `install` with `-q` (quiet: print less), `--no-deps` (do not install or resolve dependencies), `-e` (editable install (link to the source) / extended regex / stop on error, by program), `.`.
- Recipe line: runs touch, which creates an empty file or refreshes its date with `$@`.

`Makefile` lines 23 to 23:

```make
install: $(STAMP) ## create .venv from the hash-pinned lock file
```

- Defines the target `install`. It needs `$(STAMP)` to be ready first. Its help text is "create .venv from the hash-pinned lock file".

`Makefile` lines 25 to 26:

```make
env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }
```

- Defines the target `env`. It has no prerequisites.
- Recipe line: tests a condition: `-f .env`; if that fails, it runs cp, which copies files with `.env.example`, `.env`; then it prints `created .env from .env.example`. (the leading `@` stops Make from printing the command first)

`Makefile` lines 28 to 28:

```make
up: env $(STAMP) ## prepare the environment (there are no services to start)
```

- Defines the target `up`. It needs `env $(STAMP)` to be ready first. Its help text is "prepare the environment (there are no services to start)".

`Makefile` lines 30 to 31:

```make
db: $(STAMP) ## create the merchant's order table with sql/001_schema.sql and the sample rows of sql/002_seed.sql
	$(CLI) db
```

- Defines the target `db`. It needs `$(STAMP)` to be ready first. Its help text is "create the merchant's order table with sql/001_schema.sql and the sample rows of sql/002_seed.sql".
- Recipe line: runs the project's command-line program with the subcommand `db`.

`Makefile` lines 33 to 34:

```make
run: up ## the lesson's scenario: naive checkout, redesign, proof, scope, evidence pack, verification
	$(CLI) demo
```

- Defines the target `run`. It needs `up` to be ready first. Its help text is "the lesson's scenario: naive checkout, redesign, proof, scope, evidence pack, verification".
- Recipe line: runs the project's command-line program with the subcommand `demo`.

`Makefile` lines 36 to 37:

```make
verify: $(STAMP) ## check that every requirement maps to evidence and every file says what it should
	$(CLI) verify
```

- Defines the target `verify`. It needs `$(STAMP)` to be ready first. Its help text is "check that every requirement maps to evidence and every file says what it should".
- Recipe line: runs the project's command-line program with the subcommand `verify`.

`Makefile` lines 39 to 40:

```make
scope: $(STAMP) ## print the cardholder data environment before and after, and what changed
	$(CLI) scope
```

- Defines the target `scope`. It needs `$(STAMP)` to be ready first. Its help text is "print the cardholder data environment before and after, and what changed".
- Recipe line: runs the project's command-line program with the subcommand `scope`.

`Makefile` lines 42 to 43:

```make
scan: $(STAMP) ## search a folder for card numbers: make scan PATHS="state evidence"
	$(CLI) scan $(PATHS)
```

- Defines the target `scan`. It needs `$(STAMP)` to be ready first. Its help text is "search a folder for card numbers: make scan PATHS="state evidence"".
- Recipe line: runs the project's command-line program with the subcommand `scan` with `$(PATHS)`.

`Makefile` lines 45 to 46:

```make
queries: db ## run sql/003_queries.sql against the sample database
	sqlite3 $(DATABASE_PATH) < sql/003_queries.sql
```

- Defines the target `queries`. It needs `db` to be ready first. Its help text is "run sql/003_queries.sql against the sample database".
- Recipe line: runs the SQLite command-line shell with `$(DATABASE_PATH)`, reading its input from `sql/003_queries.sql`.

`Makefile` lines 48 to 49:

```make
serve-provider: $(STAMP) ## run the local payment provider on its port
	$(CLI) serve provider
```

- Defines the target `serve-provider`. It needs `$(STAMP)` to be ready first. Its help text is "run the local payment provider on its port".
- Recipe line: runs the project's command-line program with the subcommand `serve` with `provider`.

`Makefile` lines 51 to 52:

```make
serve-merchant: $(STAMP) ## run the redesigned merchant on its port
	$(CLI) serve merchant
```

- Defines the target `serve-merchant`. It needs `$(STAMP)` to be ready first. Its help text is "run the redesigned merchant on its port".
- Recipe line: runs the project's command-line program with the subcommand `serve` with `merchant`.

`Makefile` lines 54 to 55:

```make
serve-naive: $(STAMP) ## run the naive checkout (to be measured, test card only)
	$(CLI) serve naive
```

- Defines the target `serve-naive`. It needs `$(STAMP)` to be ready first. Its help text is "run the naive checkout (to be measured, test card only)".
- Recipe line: runs the project's command-line program with the subcommand `serve` with `naive`.

`Makefile` lines 57 to 58:

```make
docker-build: ## build the image of the three apps
	docker build -t compliance-shrink-pci-scope:dev .
```

- Defines the target `docker-build`. It has no prerequisites. Its help text is "build the image of the three apps".
- Recipe line: runs Docker with the subcommand `build` with `-t compliance-shrink-pci-scope:dev` (tag (name) the image / tuples only, by program), `.`.

`Makefile` lines 60 to 62:

```make
test: $(STAMP) ## unit tests with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest tests/unit --cov=pci_scope --cov-report=term
	$(PY) -m coverage report --include='src/pci_scope/domain/*,src/pci_scope/application/*' --fail-under=95
```

- Defines the target `test`. It needs `$(STAMP)` to be ready first. Its help text is "unit tests with coverage (domain and application must stay at 95% or more)".
- Recipe line: runs pytest, the test runner with `tests/unit`, `--cov=pci_scope` (measure coverage of this package), `--cov-report=term` (how to print the coverage report) (run through the project's Python with `-m`).
- Recipe line: runs coverage.py, which measures which lines the tests ran with `report`, `--include=src/pci_scope/domain/*,src/pci_scope/application/*` (only these files), `--fail-under=95` (exit with an error if the total is lower than this percent) (run through the project's Python with `-m`).

`Makefile` lines 64 to 65:

```make
test-e2e: $(STAMP) ## the scenario against real local servers (provider, merchant, naive)
	$(PY) -m pytest tests/e2e -m e2e
```

- Defines the target `test-e2e`. It needs `$(STAMP)` to be ready first. Its help text is "the scenario against real local servers (provider, merchant, naive)".
- Recipe line: runs pytest, the test runner with `tests/e2e`, `-m e2e` (run a module (or select tests by marker for pytest)) (run through the project's Python with `-m`).

`Makefile` lines 67 to 71:

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports
```

- Defines the target `lint`. It needs `$(STAMP)` to be ready first. Its help text is "ruff check, ruff format check, mypy, import-linter".
- Recipe line: runs ruff, the linter and formatter with `check`, `.`.
- Recipe line: runs ruff, the linter and formatter with `format`, `--check` (report only; change nothing), `.`.
- Recipe line: runs mypy, the type checker.
- Recipe line: runs import-linter, the architecture rule checker.

`Makefile` lines 73 to 75:

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

- Defines the target `format`. It needs `$(STAMP)` to be ready first. Its help text is "apply ruff's formatting and safe fixes".
- Recipe line: runs ruff, the linter and formatter with `check`, `--fix` (apply the fixes that are safe), `.`.
- Recipe line: runs ruff, the linter and formatter with `format`, `.`.

`Makefile` lines 77 to 78:

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- Defines the target `audit`. It needs `$(STAMP)` to be ready first. Its help text is "check the locked dependencies for known vulnerabilities".
- Recipe line: runs pip-audit, the vulnerability scanner with `--no-deps` (do not install or resolve dependencies), `--disable-pip` (do not use pip to resolve), `-r requirements-dev.lock` (read the list from the named file).

`Makefile` lines 80 to 80:

```make
check: lint test ## everything CI runs apart from the audit
```

- Defines the target `check`. It needs `lint test` to be ready first. Its help text is "everything CI runs apart from the audit".

`Makefile` lines 82 to 83:

```make
down: ## remove generated output (nothing is running)
	rm -rf build
```

- Defines the target `down`. It has no prerequisites. Its help text is "remove generated output (nothing is running)".
- Recipe line: runs rm, which deletes files with `-rf` (delete folders and everything inside without asking), `build`.

`Makefile` lines 85 to 86:

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage htmlcov
```

- Defines the target `clean`. It needs `down` to be ready first.
- Recipe line: runs rm, which deletes files with `-rf` (delete folders and everything inside without asking), `$(VENV)`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.import_linter_cache`, `.coverage`, `htmlcov`.

## Try it yourself

From the repository root:

```bash
make help
```
Expect one line per documented target: `audit`, `check`, `db`, `docker-build`, `down`, `format`, `help`, `install`, `lint`, `queries`, `run`, `scan`, `serve-merchant`, `serve-naive`, `serve-provider`, `test`, `test-e2e`, `up`, `verify`, each followed by a tab and its description.

```bash
make -n test
```
`-n` is a dry run: Make prints the commands it would run and runs none. Expect two lines: the `pytest` line and the
`coverage report` line, with `.venv/bin/python` at the start.

```bash
make -n down
```
Expect `rm -rf build`.

```bash
ls -l .venv/.installed
```
Expect a file of size 0 (after a first `make up`). Run `touch pyproject.toml`, then `make -n up`: Make now shows the
install commands again, because `pyproject.toml` is newer than the marker.

```bash
make run
```
Expect the scenario's output: the scope before and after, `order statuses: ...`, the list of evidence files, and `OK: ... requirements, ... files, 0 problem(s)`.

## Mistakes people make

- **Spaces instead of a tab** in a recipe. Make answers `missing separator`. The `.editorconfig` entry for
  `Makefile` prevents it in most editors.
- **Expecting `cd` to carry over** between recipe lines. It does not; each line has its own shell.
- **Forgetting `.PHONY`** for a target that is not a file. This Makefile lists every command target there.
- **Typing `$VAR` instead of `$(VAR)`** for a Make variable.
- **Running `make` with no target.** It builds the first target in the file, which here is `help`, a harmless choice
  on purpose.

## Check yourself

1. Why does `make test` not reinstall the packages every time?
   **Answer:** The `.venv/.installed` marker is a prerequisite. Make only reruns the install recipe when the lock file or `pyproject.toml` is newer than the marker.
2. What does `export` on its own line do?
   **Answer:** It passes every Make variable, including those read from `.env`, to the programs Make starts.
3. What would break if `.PHONY` did not list `test` and someone created a file named `test`?
   **Answer:** Make would see an existing file with no newer prerequisites and say `test` is up to date, skipping the tests.
4. What does the `@` at the start of a recipe line do?
   **Answer:** It stops Make from printing the command before running it.
5. Why is `check` written with no recipe?
   **Answer:** It only names `lint` and `test` as prerequisites, so running it runs both.

## Further reading

- GNU Make manual: <https://www.gnu.org/software/make/manual/make.html> (this repository is developed with the GNU-compatible Make that ships with macOS and with Ubuntu).
