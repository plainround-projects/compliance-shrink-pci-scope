# The payment provider's API: tokens, intents, hosted fields, webhooks

## What it is

A **payment provider** takes card details so that your server does not have to. Instead of a card number you hold **tokens**: opaque ids such as
`cus_...` (a customer), `pm_...` (a saved payment method) and `pi_...` (one **payment intent**: "collect 19.00 EUR from this customer"). **Hosted fields** are
card inputs served by the provider (in an iframe) so the card goes browser to provider directly. A **webhook** is the provider calling
your server to say a payment succeeded or failed. This repository uses a **local stand-in** for such a provider in test mode, with the same shape of
API (no real provider is called).

## Why this repository uses it

Keeping the card off your side is the way to shrink PCI scope: if your page, server, logs, database and backups never touch card data, far
fewer systems and teams carry the security requirements. The stand-in lets the whole flow run on a laptop, offline, with the published
test card only.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/provider_app.py` | The stand-in provider: `/v1/customers`, `/v1/payment_methods`, `/v1/payment_intents`, `/confirm`, `/v1/refunds`, `/frame`, `/v1/elements.js`. |
| `src/pci_scope/infrastructure/provider_http.py` | The merchant's client for the provider's server-side API. |
| `src/pci_scope/application/checkout.py` | The merchant's flow: start, complete, charge again, refund, handle an event. |
| `docs/adr/0001-a-local-stand-in-for-the-provider.md` | Why a stand-in, and what it does not claim. |
| `docs/provider-attestation.md`, `docs/responsibilities.md` | What the provider answers for and what stays with the merchant. |

## How it works underneath

1. The merchant's server asks the provider (with the **secret key**) to create a customer and a payment intent. The provider returns the
   intent's id and a **client secret**.
2. The page loads the provider's script; the script opens the provider's iframe. The customer types the card **into the iframe**.
3. The frame sends the card to the provider (`/v1/payment_methods`, with the **publishable key**) and receives a `pm_...` token; then it
   confirms the intent.
4. The page returns to the merchant's `/done`; the merchant asks the provider for the intent and records the status. The provider also sends a
   **signed webhook**.
5. Later the merchant can **charge again** or **refund** using only the tokens.

## Walkthrough of this repository's use

`src/pci_scope/interfaces/provider_app.py`:

```python
    @app.post("/v1/payment_methods")
    def create_method() -> tuple[Response, int] | Response:
        if not publishable_ok():
            return error(401, "authentication_error", "Invalid publishable key")
        number = request.form.get("card[number]", "").replace(" ", "")
        if not luhn_valid(number) or not request.form.get("card[cvc]"):
            return error(400, "card_error", "Your card number is incorrect.")
        method = _id("pm")
        state.methods[method] = {"brand": "visa", "last4": number[-4:], "decline": number == DECLINED_TEST_CARD}
```

The only route that receives a card. It checks the publishable key, the Luhn check and a CVC, and **keeps only the brand and the last four
digits** (`number[-4:]`): this stand-in never stores a full number. It returns a `pm_` token.

`src/pci_scope/interfaces/provider_app.py`:

```python
    @app.post("/v1/payment_intents")
    def create_intent() -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        form = request.form
        if not form.get("amount", "").isdigit() or not form.get("currency"):
            return error(400, "invalid_request_error", "amount and currency are required")
        intent_id = _id("pi")
        intent: dict[str, Any] = {
            "id": intent_id,
            "client_secret": f"{intent_id}_secret_{secrets.token_hex(8)}",
            "amount": int(form["amount"]),
            "currency": form["currency"],
            "customer": form.get("customer"),
```

Creating an intent needs the **secret** key and an amount and currency. The intent starts as `requires_payment_method`.

`src/pci_scope/interfaces/provider_app.py`:

```python
            if form.get("confirm") == "true":
                method = state.methods.get(form.get("payment_method", ""))
                if method is None or form.get("customer") not in state.customers or form.get("off_session") != "true":
                    return error(
                        400,
                        "invalid_request_error",
                        "a saved payment method and customer are required to charge off-session",
                    )
                intent["status"] = "requires_payment_method" if method["decline"] else "succeeded"
                emit("payment_intent.payment_failed" if method["decline"] else "payment_intent.succeeded", intent)
```

A **repeat charge** (`confirm=true`, `off_session=true`) works from tokens alone: it needs a saved payment method and a known customer, and
no card data at all.

`src/pci_scope/application/checkout.py`:

```python
    def charge_again(self, intent_id: str) -> Order:
        """Take a second payment from the saved payment method, using only the customer and method tokens."""
        order = self._known(intent_id)
        if not order.payment_method_id or not order.customer_id:
            raise PaymentError("no saved payment method for this order")
        intent = self._provider.charge_saved(
            order.customer_id, order.payment_method_id, order.amount_cents, order.currency
        )
        self._orders.create(intent.id, order.amount_cents, order.currency, order.customer_id)
```

The merchant side of the same: only `order.customer_id` and `order.payment_method_id` are sent.

`src/pci_scope/interfaces/provider_app.py`:

```python
    @app.post("/v1/refunds")
    def refund() -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        intent = state.intents.get(request.form.get("payment_intent", ""))
        if intent is None or intent["status"] != "succeeded":
            return error(400, "invalid_request_error", "only a succeeded payment can be refunded")
        refund_id = _id("re")
        state.refunds[refund_id] = intent["id"]
```

A refund names the intent; only a succeeded payment can be refunded.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output follows from the files quoted above and from the README's verified runs.


```bash
cat evidence/payment-summary.txt
```
Shows the eight requests of one payment (this one needs no server); only the `POST .../v1/payment_methods` carries card fields, and it goes to the provider.

```bash
cat evidence/token-storage.txt
```
Shows the merchant's order columns and rows: tokens and a status, no card number.

```bash
.venv/bin/python - <<'EOF'
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app
app = create_provider_app(ProviderState("sk_test_x", "pk_test_x", "w" * 32, "http://127.0.0.1:1/webhook", deliver=lambda *a: None))
c = app.test_client()
print(c.post("/v1/customers").status_code)
print(c.post("/v1/customers", headers={"Authorization": "Bearer sk_test_x"}).get_json()["id"][:4])
r = c.post("/v1/payment_methods", data={"card[number]": "4242424242424242", "card[cvc]": "123"}, headers={"X-Publishable-Key": "pk_test_x"})
print(r.get_json())
EOF
```
Prints `401`, `cus_` and `{'card': {'brand': 'visa', 'last4': '4242'}, 'id': 'pm_...'}`: the provider keeps only the brand and last four.

```bash
make test-e2e
```
Runs the whole flow against three real local servers.

## Mistakes people make

- **Using the secret key in the browser.** Only the publishable key may be there.
- **Trusting the redirect.** The merchant asks the provider for the final status.
- **Keeping the CVC or full number "for convenience".** The point is that you never hold them.
- **Treating the stand-in as the real thing.** It states what it does not claim (ADR 0001): no 3-D Secure, no retries for days, one worker.
- **Accepting webhooks without verifying them.** See `hmac-and-hashing.md`.

## Check yourself

1. What are `cus_`, `pm_` and `pi_`?
   **Answer:** Tokens for a customer, a saved payment method and a payment intent.
2. What is a hosted field?
   **Answer:** A card input served by the provider, in an iframe, so the card never touches the merchant.
3. How can a repeat charge work with no card data?
   **Answer:** The provider charges the saved payment method named by the token.
4. Which key creates an intent and which creates a payment method?
   **Answer:** The secret key creates intents (server side); the publishable key creates payment methods (browser side).
5. Why does the merchant ask the provider for the result?
   **Answer:** The browser's word cannot be trusted.

## Further reading

- PCI Security Standards Council, documents library (SAQ A and SAQ A-EP, e-commerce guidance): <https://www.pcisecuritystandards.org/document_library/>
- Each real payment provider documents its own API, hosted fields and test cards; this repository deliberately names none.
