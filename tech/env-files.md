# Environment variables and .env files

## What it is

An **environment variable** is a named text value that every program started from a shell can read. A **`.env` file** is a plain file of `NAME=value`
lines that tools load into the environment. Make reads `.env` and passes it on; Docker Compose reads it to fill `${...}` placeholders.

## Why this repository uses it

Twelve-factor configuration: settings live in the environment and are validated once at start-up, and keys never live in code. This repository adds
a stricter rule: **a live key is refused**, because the project is for test mode only. (The values in `.env.example` are development placeholders with the
`sk_test_` and `pk_test_` prefixes; this note describes the variables from `settings.py` and `docker-compose.yml`.)

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `.env.example` | Committed. Lists the settings with development values. (Not quoted in this note.) |
| `.env` | Local copy created by `make env`; ignored by git. |
| `Makefile` | `-include .env` and `export`. |
| `docker-compose.yml` | `${PROVIDER_SECRET_KEY:?set it in .env}` and friends. |
| `src/pci_scope/infrastructure/settings.py` | Reads and validates the environment. |

## How it works underneath

- Make reads `.env` as variable assignments and, because of `export`, copies them into the environment of every command it starts. A value in
  `.env` takes priority over a variable of the same name already in your shell (unless you use `make -e`).
- Docker Compose reads `.env` itself to fill placeholders.
- The program receives its environment at start-up; `os.environ` is a dictionary of strings.
- A missing or unusable value stops the program at once with exit code 2 and a message that names the variable.

## Walkthrough of this repository's use

`src/pci_scope/infrastructure/settings.py`:

```python
def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    if not value:
        raise SettingsError(f"{name} is required")
    return value
```

`_required` fails with `NAME is required` when a value is empty.

`src/pci_scope/infrastructure/settings.py`:

```python
def load_settings(env: Mapping[str, str]) -> Settings:
    """Validate and collect the settings. A live key is refused: this project is for test mode only."""
    secret, publishable = _required(env, "PROVIDER_SECRET_KEY"), _required(env, "PROVIDER_PUBLISHABLE_KEY")
    if not secret.startswith("sk_test_") or not publishable.startswith("pk_test_"):
        raise SettingsError("only test-mode keys (sk_test_..., pk_test_...) are accepted; never use a live key here")
    webhook = _required(env, "WEBHOOK_SECRET")
    if len(webhook) < 32:
        raise SettingsError("WEBHOOK_SECRET must be at least 32 characters")
    level = env.get("LOG_LEVEL", "INFO").upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        raise SettingsError(f"LOG_LEVEL must be DEBUG, INFO, WARNING or ERROR, got {level!r}")
    return Settings(
```

- The **secret key** must start with `sk_test_` and the **publishable key** with `pk_test_`; anything else (a live key) is refused with
  `only test-mode keys ... are accepted; never use a live key here`.
- `WEBHOOK_SECRET` must be at least 32 characters.
- `LOG_LEVEL` must be one of four words.

`src/pci_scope/infrastructure/settings.py`:

```python
    return Settings(
        provider_base_url=_required(env, "PROVIDER_BASE_URL").rstrip("/"),
        provider_public_url=env.get("PROVIDER_PUBLIC_URL", _required(env, "PROVIDER_BASE_URL")).rstrip("/"),
        secret_key=secret,
        publishable_key=publishable,
        webhook_secret=webhook,
        merchant_base_url=_required(env, "MERCHANT_BASE_URL").rstrip("/"),
        naive_base_url=env.get("NAIVE_BASE_URL", "http://127.0.0.1:5002").rstrip("/"),
        database_path=Path(env.get("DATABASE_PATH", "state/merchant.db")),
        naive_log_path=Path(env.get("NAIVE_LOG_PATH", "state/naive/requests.log")),
        state_dir=Path(env.get("STATE_DIR", "state")),
        evidence_dir=Path(env.get("EVIDENCE_DIR", "evidence")),
        log_level=level,
    )
```

The addresses (`PROVIDER_BASE_URL`, `PROVIDER_PUBLIC_URL`, `MERCHANT_BASE_URL`, `NAIVE_BASE_URL`) have trailing slashes removed with `.rstrip("/")`.
`PROVIDER_PUBLIC_URL` is the address a browser uses; `PROVIDER_BASE_URL` is the address the merchant's server uses (inside Docker they differ). The
rest are paths with defaults (`DATABASE_PATH`, `NAIVE_LOG_PATH`, `STATE_DIR`, `EVIDENCE_DIR`).

`docker-compose.yml`:

```yaml
  environment: &env
    PROVIDER_SECRET_KEY: ${PROVIDER_SECRET_KEY:?set it in .env}
    PROVIDER_PUBLISHABLE_KEY: ${PROVIDER_PUBLISHABLE_KEY:?set it in .env}
    WEBHOOK_SECRET: ${WEBHOOK_SECRET:?set it in .env}
    PROVIDER_BASE_URL: http://provider:5001
    PROVIDER_PUBLIC_URL: http://127.0.0.1:5001
    MERCHANT_BASE_URL: http://merchant:5000
```

In Compose, the three secrets come from `.env` (`:?` stops with a message if one is missing) and the addresses are fixed for the container network.

## Try it yourself

```bash
PROVIDER_SECRET_KEY=sk_live_x PROVIDER_PUBLISHABLE_KEY=pk_live_x WEBHOOK_SECRET=$(printf 'w%.0s' {1..32}) PROVIDER_BASE_URL=http://x MERCHANT_BASE_URL=http://y .venv/bin/pci-scope scope; echo "exit: $?"
```
Prints `configuration error: only test-mode keys (sk_test_..., pk_test_...) are accepted; never use a live key here` and `exit: 2`.

```bash
git check-ignore -v .env
```
Prints the `.gitignore` line that ignores `.env`.

```bash
grep -n "_required\|startswith\|at least" src/pci_scope/infrastructure/settings.py | head -6
```
Shows where settings are required and checked.

```bash
make scope | head -3
```
Loads `.env` through Make and prints the first lines of the scope report.

## Mistakes people make

- **Committing `.env`.** It is in `.gitignore`; only `.env.example` is committed, with development placeholders.
- **Using a live key.** The program refuses it.
- **Expecting the shell to override `.env` inside `make`.** The value in `.env` wins unless you use `make -e`.
- **Confusing the two provider addresses.** The browser uses `PROVIDER_PUBLIC_URL`; the merchant's server uses `PROVIDER_BASE_URL`.
- **A short webhook secret.** The loader refuses under 32 characters.

## Check yourself

1. What stops a live key from being used?
   **Answer:** `load_settings` accepts only `sk_test_` and `pk_test_` prefixes.
2. Why are there two provider addresses?
   **Answer:** The browser and the merchant's server reach the provider by different addresses (inside Docker they differ).
3. What does `${VAR:?message}` do in Compose?
   **Answer:** Stops with the message if the variable is not set.
4. Why is `.env` ignored by git?
   **Answer:** It is local and may hold real values.
5. What is the minimum length of `WEBHOOK_SECRET`?
   **Answer:** 32 characters.

## Further reading

- The Twelve-Factor App, III. Config: <https://12factor.net/config>
- Docker Compose, environment variables: <https://docs.docker.com/compose/how-tos/environment-variables/>
- GNU Make, `include` and `export`: <https://www.gnu.org/software/make/manual/make.html#Include>
