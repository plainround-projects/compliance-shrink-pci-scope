# gunicorn 26

## What it is

gunicorn ("Green Unicorn") is a **WSGI HTTP server**: it listens on a port, receives HTTP requests, and hands each to a Python web
application through the WSGI interface. It starts a **master** process that starts **worker** processes; with `--threads` each worker
can also handle several requests at once.

## Why this repository uses it

One image runs three different apps (`provider`, `merchant`, `naive`). The start command chooses the app from an environment variable and
the worker count from the app: the provider keeps its state in memory, so it must run with **one** worker.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Dockerfile` | `CMD ["sh", "-c", "exec gunicorn ..."]`. |
| `src/pci_scope/interfaces/factories.py` | `provider()`, `merchant()`, `naive()`: zero-argument factories. |
| `pyproject.toml`, `requirements.lock` | `gunicorn>=23`, `gunicorn==26.2.0`. |

## How it works underneath

`gunicorn "module:factory()"` imports the module, calls the factory to get the WSGI app, and serves it. Each worker is a separate
process with its own memory, so state held in a variable is **not shared** between workers. On `SIGTERM` (what Docker sends to stop a
container) gunicorn lets workers finish current requests within `--graceful-timeout`.

## Walkthrough of this repository's use

`Dockerfile`:

```dockerfile
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:$PORT --workers $([ \"$APP\" = provider ] && echo 1 || echo 2) --threads 8 --timeout 30 --graceful-timeout 20 --no-control-socket \"pci_scope.interfaces.factories:$APP()\""]
```

The start command, in pieces:
- `["sh", "-c", "..."]` runs the string through a shell, so the shell can substitute `$PORT` and `$APP`.
- `exec gunicorn ...` replaces the shell with gunicorn (process 1), so gunicorn receives the stop signal directly.
- `--bind 0.0.0.0:$PORT`: listen on all interfaces **inside the container**; Compose publishes the port on the host's `127.0.0.1` only.
- `--workers $([ "$APP" = provider ] && echo 1 || echo 2)`: **command substitution**. `$(...)` runs a command and uses its output. `[ "$APP" =
  provider ]` is true for the provider, so `echo 1`; otherwise `echo 2`. One worker for the provider (state in memory), two for the others.
- `--threads 8`: eight threads per worker.
- `--timeout 30` and `--graceful-timeout 20`: restart a silent worker after 30 s; give workers 20 s to finish on a stop signal.
- `--no-control-socket`: do not create gunicorn's control socket file; the container's file system is read-only, so it could not be created.
- `"pci_scope.interfaces.factories:$APP()"`: the factory to call: `provider()`, `merchant()` or `naive()`.

`src/pci_scope/interfaces/factories.py`:

```python
def provider() -> Flask:
    """The local payment provider. State is in memory, so run it with one worker."""
    settings = load_settings(os.environ)
    configure_logging(settings.log_level)
    state = ProviderState(
        settings.secret_key, settings.publishable_key, settings.webhook_secret, f"{settings.merchant_base_url}/webhook"
    )
```

The factory reads the settings from the environment, configures logging, builds the provider's state and returns the Flask app. The
docstring states the reason for one worker.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output follows from the files quoted above and from the README's verified runs.

```bash
.venv/bin/gunicorn --version
```
Prints `gunicorn (version 26.2.0)`.

```bash
.venv/bin/gunicorn --help | grep -A1 -- "--no-control-socket"
```
Prints the option's description for the pinned version.

```bash
sh -c 'APP=provider; echo --workers $([ "$APP" = provider ] && echo 1 || echo 2); APP=merchant; echo --workers $([ "$APP" = provider ] && echo 1 || echo 2)'
```
Prints `--workers 1` and `--workers 2`: the substitution from the Dockerfile, run by itself (needs no Docker).

```bash
docker compose up --build
```
Starts the provider and the merchant; open `http://127.0.0.1:5000`. Then `docker compose down -v`.

## Mistakes people make

- **Several workers for an app with state in memory.** Each would have different data.
- **Shell-form commands that keep the shell as process 1**, so signals do not reach gunicorn. `exec` fixes it.
- **Using the development server in production.**
- **Forgetting that `0.0.0.0` inside a container is not exposed outside** until the port is published; Compose publishes it on `127.0.0.1`.

## Check yourself

1. Why does the provider run with one worker?
   **Answer:** Its state is in memory; a second process would hold different data.
2. What does `exec` do in `sh -c "exec gunicorn ..."`?
   **Answer:** Replaces the shell with gunicorn so it receives signals.
3. What does `$(...)` do?
   **Answer:** Runs the command and substitutes its output.
4. What does `module:factory()` tell gunicorn?
   **Answer:** Import the module and call the factory to get the app.
5. Why `--no-control-socket`?
   **Answer:** The read-only file system cannot hold the socket file.

## Further reading

- gunicorn 26 documentation: <https://docs.gunicorn.org/en/stable/>
- Settings: <https://docs.gunicorn.org/en/stable/settings.html>
- Deploying Flask with gunicorn: <https://flask.palletsprojects.com/en/stable/deploying/gunicorn/>
