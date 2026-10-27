# Threads, sockets and local servers

## What it is

A **thread** is a second line of execution inside one program: two things run "at the same time". A **lock** lets only one thread use
shared data at once. A **socket** is one end of a network connection; every server listens on a **port** (a number) of an address.
Port 0 asks the operating system to pick any free port.

## Why this repository uses it

The proof must use **real HTTP between real servers**: the provider, the merchant and the naive checkout run in the test process, each
on its own port, while a scripted browser talks to them. Threads let one test process host all three.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/servers.py` | `free_port()` and `LocalServer`. |
| `src/pci_scope/interfaces/provider_app.py` | A `Lock` around the provider's shared state. |
| `src/pci_scope/interfaces/demo.py`, `tests/e2e/` | Start the servers as context managers. |

## How it works underneath

`socket.socket()` opens an endpoint; `bind(("127.0.0.1", 0))` asks for any free port on the local machine; `getsockname()` tells which was
given. `make_server(host, port, app, threaded=True)` creates a server that handles each request in its own thread. `serve_forever()` blocks,
so it runs in a background thread; `daemon=True` makes that thread die with the program; `shutdown()` asks it to stop and `join()` waits.
A `with threading.Lock():` block lets one thread at a time through it.

## Walkthrough of this repository's use

`src/pci_scope/interfaces/servers.py`:

```python
def free_port() -> int:
    """A port nobody is listening on right now."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])
```

Open a socket, bind port 0, read the port the system chose, and let the socket close. There is a small race (another program could take
the port before the server does), which is acceptable for a test on a developer machine.

`src/pci_scope/interfaces/servers.py`:

```python
class LocalServer:
    """A Flask app served on 127.0.0.1:<port> until the context exits; shutdown waits for in-flight requests."""

    def __init__(self, app: Flask, port: int) -> None:
        logging.getLogger("werkzeug").setLevel(
            logging.WARNING
        )  # no access log: a URL is one more place for data to land
        self._server: BaseWSGIServer = make_server("127.0.0.1", port, app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self.url = f"http://127.0.0.1:{port}"

    def __enter__(self) -> LocalServer:
```

- `make_server("127.0.0.1", port, app, threaded=True)` (from Werkzeug) builds the server, bound to the local address only.
- `threading.Thread(target=self._server.serve_forever, daemon=True)` is the background thread that runs it.
- `self.url` is the address the test and the scripted browser use.

`src/pci_scope/interfaces/servers.py`:

```python
    def __enter__(self) -> LocalServer:
        self._thread.start()
        return self

    def __exit__(
        self, kind: type[BaseException] | None, value: BaseException | None, trace: TracebackType | None
    ) -> None:
        self._server.shutdown()
        self._thread.join(timeout=5)
        self._server.server_close()
```

`__enter__` starts the thread; `__exit__` calls `shutdown()` (which waits for requests in flight), joins the thread (at most 5 s) and
closes the socket. A test uses it as `with LocalServer(app, port) as server:`.

`src/pci_scope/interfaces/provider_app.py`:

```python
        with state.lock:
            state.intents[intent_id] = intent
            if form.get("confirm") == "true":
```

The provider keeps intents in dictionaries in memory. Because the server is threaded, two requests could change them at once; the lock
makes each change a unit. (In production the provider runs with **one** gunicorn worker for this reason, see `gunicorn.md`.)

## Try it yourself

```bash
.venv/bin/python -c "from pci_scope.interfaces.servers import free_port; print(free_port() > 1023)"
```
Prints `True`: a free, non-privileged port.

```bash
.venv/bin/python - <<'EOF'
import json, urllib.request
from pci_scope.interfaces.servers import LocalServer, free_port
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app
app = create_provider_app(ProviderState("sk_test_x", "pk_test_x", "w" * 32, "http://127.0.0.1:1/webhook"))
with LocalServer(app, free_port()) as server:
    print(json.load(urllib.request.urlopen(server.url + "/healthz")))
EOF
```
Prints `{'status': 'ok'}` and exits: the server started in a thread, answered, and stopped.

```bash
.venv/bin/python -c "import threading; print(threading.active_count())"
```
Prints `1`: only the main thread.

```bash
.venv/bin/pytest -q tests/e2e
```
Runs the whole scenario against three servers.

## Mistakes people make

- **Hard-coded ports** that clash between runs or between people. `free_port()` asks the system.
- **Forgetting to shut down**, leaving the port busy. `LocalServer` is a context manager.
- **Sharing mutable data between threads without a lock.**
- **Binding to `0.0.0.0` in a test**, which exposes the port. These servers bind to `127.0.0.1`.

## Check yourself

1. What does binding to port 0 do?
   **Answer:** Asks the operating system for any free port.
2. Why is the server thread a daemon?
   **Answer:** It dies with the program instead of keeping it alive.
3. What does `shutdown()` wait for?
   **Answer:** Requests already in flight.
4. What is a lock for?
   **Answer:** Letting only one thread change shared data at a time.
5. Why does the production provider use one worker?
   **Answer:** Its state is in memory, so a second process would have a different state.

## Further reading

- `threading` (Python 3.12): <https://docs.python.org/3.12/library/threading.html>
- `socket`: <https://docs.python.org/3.12/library/socket.html>
- Werkzeug, `make_server`: <https://werkzeug.palletsprojects.com/en/stable/serving/>
