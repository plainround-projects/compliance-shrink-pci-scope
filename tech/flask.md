# Flask 3.1

## What it is

Flask is a small Python **web framework**: it receives HTTP requests, finds the function registered for the path (a **route**), calls
it, and turns the return value into a response. It follows the **WSGI** standard, so any WSGI server (gunicorn, Werkzeug's own server)
can run it.

## Why this repository uses it

Three small web apps are needed: the naive checkout (the "before"), the redesigned merchant, and a local stand-in for a payment
provider with hosted card fields. Flask makes each a page of code and keeps the framework out of the rules.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/merchant_app.py` | `create_merchant_app`: the page, `/create-payment`, `/done`, `/charge-again`, `/refund`, `/webhook`. |
| `src/pci_scope/interfaces/provider_app.py` | `create_provider_app`: `/v1/...` API, `/frame`, `/v1/elements.js`. |
| `src/pci_scope/interfaces/naive_app.py` | `create_naive_app`: `/` and `/pay`. |
| `src/pci_scope/interfaces/factories.py` | One zero-argument factory per app for gunicorn. |
| `tests/unit/interfaces/test_apps.py` | Drives the apps with Flask's test client. |

## How it works underneath

`Flask(__name__)` makes an application object. A decorator such as `@app.get("/healthz")` registers the function for that path and
method. For each request Flask builds a `request` object, runs `before_request` and `after_request` hooks, calls the route, and sends
the response. A route may return a string, a `Response`, `jsonify(...)`, or `(body, status)`. If a route raises an exception, Flask looks
for an **error handler** registered for that class.

## Walkthrough of this repository's use

`src/pci_scope/interfaces/naive_app.py`:

```python
    @app.get("/")
    def checkout() -> str:
        return FORM

    @app.post("/pay")
    def pay() -> str:
        logger.info("payment request: %s", dict(request.form))  # the mistake: card data reaches the log
        return "paid (simulated)"
```

The naive app: `GET /` returns the form, `POST /pay` reads `request.form` (the posted fields) and logs them. The mistake is on the line with the comment.

`src/pci_scope/interfaces/merchant_app.py`:

```python
def create_merchant_app(checkout: CheckoutService, provider_base_url: str, publishable_key: str) -> Flask:
    """The merchant's routes. The page's content security policy names the provider and nothing else."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    policy = (
        f"default-src 'self'; script-src 'self' {provider_base_url}; frame-src {provider_base_url}; "
        f"connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    )

    @app.after_request
    def secure(response: Response) -> Response:
        response.headers["Content-Security-Policy"] = policy
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response
```

- An **application factory**: a function that builds the app from its parts.
- `MAX_CONTENT_LENGTH = 16 * 1024` makes Flask refuse bodies over 16 KiB with `413`: there is nothing a checkout page needs to send that large.
- `@app.after_request` adds security headers to **every** response: the `Content-Security-Policy` (see `content-security-policy.md`),
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` and `Cache-Control: no-store`.

`src/pci_scope/interfaces/merchant_app.py`:

```python
    @app.post("/create-payment")
    def create_payment() -> Response:
        started = checkout.start()
        logger.info("created payment %s amount=1900 eur", started.intent_id)
        return jsonify(clientSecret=started.client_secret, id=started.intent_id)

    @app.get("/done")
    def done() -> tuple[str, int]:
        order = checkout.complete(request.args.get("payment_intent", ""))
        logger.info("payment %s status=%s", order.payment_intent_id, order.status)
        return (f"payment {order.payment_intent_id}: {order.status}", 200 if order.status == "succeeded" else 402)
```

`/create-payment` asks the checkout service to create a payment and returns only the **client secret** and the id to the browser.
`/done` asks the provider what happened to the payment (the browser's word is not used) and answers `200` or `402`.

`src/pci_scope/interfaces/merchant_app.py`:

```python
    @app.post("/webhook")
    def webhook() -> Response:
        outcome = checkout.handle_event(request.get_data(), request.headers.get("Provider-Signature"), int(time.time()))
        logger.info("webhook %s", outcome)
```

`request.get_data()` returns the **raw bytes** of the body, which is what the signature covers.

`src/pci_scope/interfaces/merchant_app.py`:

```python
    @app.errorhandler(PaymentError)
    def payment_failed(problem: PaymentError) -> tuple[Response, int]:
        logger.warning("payment error: %s", problem)
        return jsonify(error=str(problem)), 402
```

Domain errors become status codes in one place; the catch-all handler (a few lines below) logs only the class name of an unexpected error
and answers `500`.

There is **no route that accepts a card number** on the merchant: the first lines of the file say so, and `route-check.txt` proves it with a `404`.

## Try it yourself

```bash
.venv/bin/python - <<'EOF'
from pathlib import Path
from pci_scope.interfaces.naive_app import create_naive_app
app = create_naive_app(Path("/tmp/naive-demo/requests.log"))
client = app.test_client()
print(client.get("/").status_code)
print(client.post("/pay", data={"card_number": "4242424242424242", "cvv": "123"}).get_data(as_text=True))
print(open("/tmp/naive-demo/requests.log").read().strip())
EOF
```
Prints `200`, `paid (simulated)` and the log line that contains the card number and CVV: the mistake, visible.

```bash
.venv/bin/python -c "from importlib import metadata; print(metadata.version('flask'))"
```
Prints `3.1.3`.

```bash
.venv/bin/pytest -q tests/unit/interfaces/test_apps.py
```
Runs the app tests (no network).

```bash
cat evidence/route-check.txt
```
Shows the proof that `POST /pay` and `GET /pay` answer 404 on the merchant.

## Mistakes people make

- **Logging the request body.** The naive app does it on purpose; the merchant never does.
- **Trusting the browser's price or status.** The price is a constant in the checkout service; the status comes from the provider.
- **A route that accepts card data** "temporarily". There is none.
- **Running Flask's development server in production.** Use gunicorn.
- **Re-serializing the webhook body before verifying.** Use the raw bytes.

## Check yourself

1. What is an application factory?
   **Answer:** A function that builds the app from its parts.
2. What does `MAX_CONTENT_LENGTH` do?
   **Answer:** Makes Flask refuse larger request bodies with `413`.
3. Why does `/done` ask the provider instead of reading the browser's claim?
   **Answer:** The browser can lie; the provider is the source of truth.
4. What does `request.get_data()` return?
   **Answer:** The raw request body in bytes.
5. What proves the merchant has no card route?
   **Answer:** `evidence/route-check.txt`: `POST /pay` and `GET /pay` return 404.

## Further reading

- Flask 3.1 documentation: <https://flask.palletsprojects.com/en/stable/>
- Application factories: <https://flask.palletsprojects.com/en/stable/patterns/appfactories/>
- Testing: <https://flask.palletsprojects.com/en/stable/testing/>
