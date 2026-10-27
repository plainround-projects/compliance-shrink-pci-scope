# argparse (the command line)

## What it is

A **command-line program** is started by typing its name and some words: `pci-scope check`. Those words are its
**arguments**. `argparse` is the standard Python module that reads them, checks them, builds the `--help` text and
reports mistakes. An **exit code** is the number a program returns to the shell when it ends: 0 means success, other
numbers mean different failures.

## Why this repository uses it

`make run` and CI decide pass or fail from the exit code, so the command must return the right number. `argparse`
gives subcommands (`check`, `report`...) and a free help text, with no extra packages.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/cli.py` | `build_parser()`, `main()` and `_run()` for `pci-scope`. |
| `pyproject.toml` `[project.scripts]` | Registers `pci-scope`. |
| `Makefile` | `$(CLI) demo`, `$(CLI) verify`, `$(CLI) scope`, `$(CLI) scan $(PATHS)`, `$(CLI) serve ...`, `$(CLI) db`. |
| `tests/unit/interfaces/test_apps.py` | Calls the apps and the CLI helpers directly. |

## How it works underneath

1. The shell starts the program with a list of words. Python puts them in `sys.argv`.
2. `parser.parse_args(argv)` walks that list: the first word picks a subcommand; options like `--write` are matched by
   name. Unknown words make `argparse` print an error and exit with code 2.
3. The result is a `Namespace` object whose attributes are the answers (`args.command`).
4. The program does its work and returns an integer. `raise SystemExit(main())` turns the integer into the process
   exit code. The shell stores it in `$?`.

## Walkthrough of this repository's use

`src/pci_scope/interfaces/cli.py`:

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

- `add_subparsers(dest="command", required=True)` creates the subcommands; the chosen one is `args.command`.
- `scan.add_argument("paths", nargs="+", type=Path)`: a **positional** argument that takes **one or more** values (`nargs="+"`), each
  converted to a `Path`. This is `pci-scope scan state evidence`.
- `serve.add_argument("app", choices=("provider", "merchant", "naive"))` limits the allowed words.

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
        return 2
```

- Exit codes (docstring at the top of the file): **0** ok, **1** findings, **2** bad input or configuration.
- Settings and catalog errors become `configuration error: ...` on stderr, exit 2; file problems (`OSError`) become `error: ...`, exit 2.

`src/pci_scope/interfaces/cli.py`:

```python
    if args.command == "scan":
        outcome = run_scan("scanning:", PathArtifacts(args.paths))
        print(outcome.text, end="")
        return outcome.exit_code
```

`scan` returns the scan's own exit code, so `pci-scope scan state evidence` exits 1 if any card number or card field is found: that is
how a build could fail on a leak.

`src/pci_scope/interfaces/cli.py`:

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

`serve` builds one of the three apps and starts it with Werkzeug's `run_simple` on the host and port taken from the configured URL
(`urlsplit(url)`). `threaded=True` lets it handle several requests at once.

## Try it yourself

```bash
.venv/bin/pci-scope --help
```
Prints the usage line and the subcommands: `demo`, `verify`, `scope`, `scan`, `serve`, `db`.

```bash
.venv/bin/pci-scope nonsense; echo "exit: $?"
```
`argparse` prints `error: argument command: invalid choice: 'nonsense'` and the shell shows `exit: 2`.

```bash
.venv/bin/pci-scope scan; echo "exit: $?"
```
`argparse` reports `the following arguments are required: paths` and `exit: 2`.

```bash
make scope | head -12
```
Prints the cardholder data environment before the redesign (it needs no server).

```bash
make scan PATHS="evidence"
```
Scans the evidence folder; prints a line per artifact and ends with a verdict of no findings.

## Mistakes people make

- **Printing errors to stdout.** Errors belong on stderr so scripts can separate them.
- **Always exiting 0**, so CI cannot tell a failure. This program returns 1 for findings and 2 for bad setup.
- **Reading `sys.argv` by hand.** `argparse` handles quoting, options and help.
- **Calling `sys.exit` deep inside the code.** Only `main` decides the exit code; the rest returns values.

## Check yourself

1. What does `nargs="+"` mean?
   **Answer:** The argument takes one or more values.
2. What does `scan` return when it finds card data?
   **Answer:** Exit code 1.
3. What does `choices=(...)` do?
   **Answer:** Limits the argument to the listed words.
4. What do exit codes 0, 1 and 2 mean in `pci-scope`?
   **Answer:** Ok; findings; bad input or configuration.
5. Why does `serve` use `urlsplit`?
   **Answer:** To get the host and port out of the configured URL.

## Further reading

- `argparse` (Python 3.12): <https://docs.python.org/3.12/library/argparse.html>
- Argparse tutorial: <https://docs.python.org/3.12/howto/argparse.html>
