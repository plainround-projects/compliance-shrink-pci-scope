# urllib (the HTTP client)

## What it is

`urllib` is Python's built-in way to make HTTP requests. `urllib.request.Request` describes a request (URL, method, headers, body);
`urllib.request.urlopen` sends it and returns a response; `urllib.error` holds the errors; `urllib.parse` builds and takes apart URLs
and form bodies.

## Why this repository uses it

The point of the project is to show who receives what. Using the plain standard-library client for everything means every byte a
"browser" sends can be recorded and checked, and nothing hides in a framework.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/infrastructure/provider_http.py` | `HttpProvider`: the merchant's server-side calls with the secret key. |
| `src/pci_scope/interfaces/provider_app.py` | `deliver_over_http`: signed webhooks. |
| `src/pci_scope/interfaces/browser_sim.py` | `Browser.request`: every request the scripted browser makes. |
| `Dockerfile` | The health check uses `urllib.request.urlopen`. |

## How it works underneath

`urlopen` opens a TCP connection to the host, sends the request text, reads the answer, and returns an object with `.status`,
`.headers` and `.read()`. A **4xx or 5xx** status raises `urllib.error.HTTPError` (which is also a response you can read); a network
problem raises `URLError` or `OSError`; a slow server raises `TimeoutError` after `timeout` seconds. `urllib.parse.urlencode(dict)` makes
`a=1&b=2` (the form encoding); `quote(text)` makes text safe inside a URL.

## Walkthrough of this repository's use

`src/pci_scope/infrastructure/provider_http.py`:

```python
    def _post(self, path: str, fields: dict[str, Any]) -> dict[str, Any]:
        return self._call("POST", path, urllib.parse.urlencode(fields).encode())

    def _call(self, method: str, path: str, body: bytes | None) -> dict[str, Any]:
        request = urllib.request.Request(
```

`urlencode(fields).encode()` turns a dictionary into a form body in bytes. The call adds the secret key as a **bearer token** header.

`src/pci_scope/infrastructure/provider_http.py`:

```python
        request = urllib.request.Request(
            self._base + path,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/x-www-form-urlencoded"},
        )
```

A request object: the URL, the body (`data=`), the method, and two headers. Retries, timeouts and error handling are walked through in
`python.md`.

`src/pci_scope/interfaces/provider_app.py`:

```python
def deliver_over_http(url: str, body: bytes, signature: str) -> None:
    """POST a webhook with a timeout; a failure is logged by the caller, never raised into the payment."""
    http = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/json", "Provider-Signature": signature}
    )
    with urllib.request.urlopen(http, timeout=5):
        pass
```

The provider POSTs the event as JSON with a `Provider-Signature` header. `with urllib.request.urlopen(http, timeout=5): pass` sends it and
closes the connection; a failure is raised and the caller decides what to do with it.

`src/pci_scope/interfaces/browser_sim.py`:

```python
        http = urllib.request.Request(url, data=body, method=method, headers=sent)
        try:
            with urllib.request.urlopen(http, timeout=self._timeout) as response:
                reply = Reply(
                    response.status, dict(response.headers), response.read().decode("utf-8", errors="replace")
                )
        except urllib.error.HTTPError as problem:
            reply = Reply(problem.code, dict(problem.headers), problem.read().decode("utf-8", errors="replace"))
        self.exchanges.append(Exchange(method, url, reply.status, (body or b"").decode()))
        return reply
```

The scripted browser turns **HTTP errors into replies** (`except urllib.error.HTTPError as problem: reply = Reply(problem.code, ...)`), so a `402` or `404`
is data, not a crash. Every request is also appended to `self.exchanges`, which becomes the HAR capture (see `har.md`).

`src/pci_scope/interfaces/browser_sim.py`:

```python
    secret = urllib.parse.quote(started["clientSecret"])
```

`quote` percent-encodes text for use inside a URL (`/` becomes `%2F`).

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output follows from the files quoted above and from the README's verified runs.

```bash
.venv/bin/python -c "import urllib.parse as p; print(p.urlencode({'card[number]': '4242 4242', 'a': 1}), p.quote('http://x/y?z'), p.urlsplit('http://127.0.0.1:5000/done?x=1').port)"
```
Prints `card%5Bnumber%5D=4242+4242&a=1`, `http%3A//x/y%3Fz` and `5000`. (This one needs no server.)

```bash
.venv/bin/python -c "import urllib.request, urllib.error
try:
    urllib.request.urlopen('http://127.0.0.1:9/', timeout=2)
except urllib.error.URLError as e:
    print(type(e).__name__)"
```
Prints `URLError`: nothing listens on port 9.

```bash
make serve-provider
```
In a second terminal: `curl -s http://127.0.0.1:5001/healthz` prints `{"status":"ok"}`. Stop the server with Ctrl+C.

```bash
.venv/bin/pytest -q tests/e2e
```
Runs the scenario against real local servers on free ports.

## Mistakes people make

- **No timeout**, so a stuck server hangs the caller. Every call here has one.
- **Retrying a 4xx.** A 4xx is the provider's answer ("your card was declined"), not a fault; only 5xx and network errors are retried.
- **Building form bodies by joining strings.** Use `urlencode`.
- **Raising on HTTP errors in a test client.** The simulated browser keeps them as replies.

## Check yourself

1. What does `urlopen` raise for a 404?
   **Answer:** `urllib.error.HTTPError`.
2. Why does the merchant retry a 503 but not a 402?
   **Answer:** A 5xx is a fault that may pass; a 4xx is the answer.
3. What does `urlencode` produce?
   **Answer:** A form body such as `a=1&b=2`, with special characters encoded.
4. Why does the scripted browser record every request?
   **Answer:** The record becomes the HAR evidence of who received what.
5. What does `timeout=` do?
   **Answer:** Gives up (raises `TimeoutError`) when the server is silent for too long.

## Further reading

- `urllib.request` (Python 3.12): <https://docs.python.org/3.12/library/urllib.request.html>
- `urllib.parse`: <https://docs.python.org/3.12/library/urllib.parse.html>; `urllib.error`: <https://docs.python.org/3.12/library/urllib.error.html>
