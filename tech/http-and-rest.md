# HTTP, forms, status codes and the provider's REST style

## What it is

**HTTP** is the way programs ask each other for things over a network. A **client** sends a **request** (a method such as `GET`, a path, headers, sometimes a
body); a **server** sends back a **response** (a **status code**, headers, a body). A **form** body is `name=value` pairs joined by `&`
(`application/x-www-form-urlencoded`). A **bearer** header carries a secret key: `Authorization: Bearer <key>`.

## Why this repository uses it

The whole lesson is about **which request carries what, and to whom**. Reading the requests is how you see whether a card number reaches
your server, so the project shows them one by one.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/browser_sim.py` | The requests a browser makes during a checkout. |
| `src/pci_scope/infrastructure/provider_http.py` | Form-encoded calls with a bearer key. |
| `src/pci_scope/interfaces/provider_app.py` | The provider's API, with its status codes. |
| `src/pci_scope/interfaces/merchant_app.py` | `200`, `402`, `404`, `413`, `500` answers. |
| `evidence/payment-summary.txt` | One line per request, with where it went. |

## How it works underneath

A request is text on a TCP connection: a first line (`POST /v1/payment_methods HTTP/1.1`), headers, a blank line and a body. The status
code says how it went: **2xx** success (200 OK), **4xx** the caller's fault (400 bad input, 401 not authenticated, 402 payment required or
failed, 404 not found, 413 too large), **5xx** the server's fault (500). Two different **origins** (scheme, host and port) are two
different parties: `http://127.0.0.1:5000` is the merchant, `http://127.0.0.1:5001` the provider.

## Walkthrough of this repository's use

`src/pci_scope/interfaces/browser_sim.py`:

```python
def pay_with_hosted_fields(
    browser: Browser, merchant: str, provider: str, publishable_key: str, card: str = TEST_CARD
) -> PaymentRun:
    """The redesigned checkout, start to finish, with the published test card typed into the provider's frame."""
    run = PaymentRun()
    page = browser.request("GET", f"{merchant}/")
    run.page_headers = page.headers
    run.page_card_fields = card_field_names(page.body)
    run.scripts = re.findall(r'<script src="([^"]+)"', page.body)
    browser.request("GET", f"{merchant}/static/checkout.js")
    browser.request("GET", f"{provider}/v1/elements.js")
    started = json.loads(browser.request("POST", f"{merchant}/create-payment").body)
    run.intent_id = started["id"]
    secret = urllib.parse.quote(started["clientSecret"])
    browser.request("GET", f"{provider}/frame?origin={urllib.parse.quote(merchant)}&client_secret={secret}")
    key = {"X-Publishable-Key": publishable_key}
    method = json.loads(
        browser.request(
            "POST",
            f"{provider}/v1/payment_methods",
            form={"card[number]": card, "card[exp_month]": "12", "card[exp_year]": "30", "card[cvc]": "123"},
            headers=key,
        ).body
    )
    browser.request(
        "POST", f"{provider}/v1/payment_intents/{run.intent_id}/confirm",
        form={"client_secret": started["clientSecret"], "payment_method": method["id"]}, headers=key,
    )  # fmt: skip
    final = browser.request("GET", f"{merchant}/done?payment_intent={run.intent_id}")
    run.final_text, run.final_status = final.body, final.status
    run.exchanges = list(browser.exchanges)
```

The redesigned checkout as the requests a browser makes, in order: load the merchant's page, its script, the provider's script; ask the
merchant to create a payment; load the provider's card frame; **send the card to the provider** (`POST {provider}/v1/payment_methods`,
with the form fields `card[number]`, `card[exp_month]`, `card[exp_year]`, `card[cvc]` and the **publishable key** in a header); confirm the
payment at the provider; return to the merchant's `/done`. Not one request to the merchant carries a card field.

`src/pci_scope/interfaces/browser_sim.py`:

```python
def pay_on_naive_checkout(browser: Browser, naive: str, card: str = TEST_CARD) -> Reply:
    """The "before": the card posted to the merchant's own server."""
    return browser.request("POST", f"{naive}/pay", form={"card_number": card, "expiry": "12/30", "cvv": "123"})
```

The "before": the card is posted to the merchant's own server.

`src/pci_scope/interfaces/provider_app.py`:

```python
    def secret_ok() -> bool:
        return request.headers.get("Authorization", "") == f"Bearer {state.secret_key}"

    def publishable_ok() -> bool:
        return (request.headers.get("X-Publishable-Key") or request.form.get("key", "")) == state.publishable_key
```

Two kinds of key: the **secret key** (server to server, sent as a bearer token) and the **publishable key** (safe in the browser, may only
create payment methods and confirm). `401` is returned for a missing or wrong key.

`src/pci_scope/domain/har.py`:

```python
def summarize(exchanges: list[Exchange], merchant: str, provider: str) -> str:
    """The lesson's summary: one line per request, where it went, and what the body held."""
    lines = []
    for item in exchanges:
        destination = origin(item.url)
```

The lesson's summary: for each request, which origin received it (`your server`, `the provider`) and which card fields its body held.

## Try it yourself

```bash
cat evidence/payment-summary.txt
```
Prints the eight requests of one payment; only the `POST .../v1/payment_methods` to the provider lists card fields.

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output follows from the files quoted above and from the README's verified runs.

```bash
make serve-provider
```
In a second terminal: `curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:5001/v1/customers` prints `401` (no key).

```bash
make test-e2e
```
Runs the whole scenario over real HTTP on local ports.

```bash
cat evidence/route-check.txt
```
Shows `POST /pay` and `GET /pay` on the merchant answering `404`.

## Mistakes people make

- **Sending the secret key to the browser.** Only the publishable key goes there.
- **Trusting what the browser says** about a price or a result. The merchant fixes the price and asks the provider for the result.
- **Putting card data in a URL**, where logs and proxies record it.
- **Returning 200 for everything.** Status codes are part of the contract.

## Check yourself

1. What is an origin?
   **Answer:** The scheme, host and port of a URL; two origins are two parties.
2. What does `401` mean?
   **Answer:** The caller is not authenticated (missing or wrong key).
3. Which key may the browser hold?
   **Answer:** The publishable key, never the secret key.
4. What is a form-encoded body?
   **Answer:** `name=value` pairs joined by `&`, with special characters percent-encoded.
5. Which request carries the card fields?
   **Answer:** `POST /v1/payment_methods` to the provider.

## Further reading

- HTTP semantics (RFC 9110): <https://www.rfc-editor.org/rfc/rfc9110>
- MDN, HTTP status codes: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status>
- URL-encoded forms: <https://url.spec.whatwg.org/#application/x-www-form-urlencoded>
