# Werkzeug, Jinja2, ItsDangerous, Blinker, Click and MarkupSafe

## What it is

Flask is built from smaller libraries, and `requirements.lock` pins each of them. **Werkzeug** handles HTTP details (requests,
responses, routing) and includes a small development server. **Jinja2** is a template engine for HTML. **MarkupSafe** escapes text for
HTML. **ItsDangerous** signs data. **Blinker** provides signals. **Click** builds command lines.

## Why this repository uses it

Flask needs them, so they are installed, pinned and hashed. This repository also imports **Werkzeug directly** in two places, to run an
app in a thread (`make_server`) and to serve it from the command line (`run_simple`).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `requirements.lock` | `werkzeug==3.1.9`, `jinja2==3.1.6`, `itsdangerous==2.2.0`, `blinker==1.9.0`, `click==8.5.0`, `markupsafe`. |
| `src/pci_scope/interfaces/servers.py` | `from werkzeug.serving import BaseWSGIServer, make_server`. |
| `src/pci_scope/interfaces/cli.py` | `from werkzeug.serving import run_simple`. |

## How it works underneath

Werkzeug's server speaks HTTP on a socket and calls the WSGI app for each request. `make_server` creates a server object you control
(`serve_forever`, `shutdown`); `run_simple` creates one and runs it until you press Ctrl+C. The development server is not hardened;
production uses gunicorn.

## Walkthrough of this repository's use

`src/pci_scope/interfaces/servers.py`:

```python
from werkzeug.serving import BaseWSGIServer, make_server
```

`src/pci_scope/interfaces/servers.py`:

```python
        self._server: BaseWSGIServer = make_server("127.0.0.1", port, app, threaded=True)
```

`make_server("127.0.0.1", port, app, threaded=True)` returns a server that handles each request in its own thread.

`src/pci_scope/interfaces/cli.py`:

```python
    run_simple(parts.hostname or "127.0.0.1", parts.port or 80, flask_app, threaded=True)
```

`run_simple(host, port, app, threaded=True)` is the one-line way to serve an app (used by `make serve-provider` and friends).

`requirements.lock`:

```text
werkzeug==3.1.9 \
    --hash=sha256:55ca7c70a75689be937aa27f8ff4b018f06ff4838fc73045560bf0f5a1291060 \
    --hash=sha256:6392e50c78460ba618e5b21f08a71f59c99ce99cdc6cf6e3dd7e6ccca8754fab
    # via flask
```

The pin: exact version, hashes, and `# via flask`.

## Try it yourself

```bash
.venv/bin/pip list 2>/dev/null | grep -iE "^(flask|werkzeug|jinja2|itsdangerous|blinker|click|markupsafe) "
```
Prints the seven packages with their versions.

```bash
.venv/bin/pip show flask | grep -E "^(Name|Version|Requires)"
```
Prints Flask's name, version and requirements.

```bash
.venv/bin/python -c "from werkzeug.routing import Map, Rule; m = Map([Rule('/v1/payment_intents/<intent_id>', endpoint='get')]).bind(''); print(m.match('/v1/payment_intents/pi_abc'))"
```
Prints `('get', {'intent_id': 'pi_abc'})`.

```bash
grep -rn "werkzeug" src | cut -c1-100
```
Shows the two direct imports.

## Mistakes people make

- **Using the Werkzeug development server in production.** It is for local use; gunicorn serves the containers.
- **Importing a transitive package without listing it.** Werkzeug is a dependency of Flask, which is why it is pinned; a package you import
  directly belongs in `pyproject.toml` too.
- **Binding a development server to all interfaces.** These servers bind to `127.0.0.1`.

## Check yourself

1. What is Werkzeug used for here?
   **Answer:** Serving apps in a thread (`make_server`) and from the command line (`run_simple`).
2. What does `threaded=True` do?
   **Answer:** Handles each request in its own thread.
3. Why are packages the code never calls still pinned?
   **Answer:** Flask imports them, so they are installed and must be reproducible.
4. What does `# via flask` mean?
   **Answer:** Flask is the reason the package is in the lock file.
5. Why not use `run_simple` in production?
   **Answer:** It is a development server.

## Further reading

- Werkzeug 3.1: <https://werkzeug.palletsprojects.com/en/stable/>
- Jinja 3.1: <https://jinja.palletsprojects.com/en/stable/>
- ItsDangerous 2.2: <https://itsdangerous.palletsprojects.com/en/stable/>
- Blinker 1.9: <https://blinker.readthedocs.io/en/stable/>
- Click 8: <https://click.palletsprojects.com/en/stable/>
- MarkupSafe: <https://markupsafe.palletsprojects.com/en/stable/>
