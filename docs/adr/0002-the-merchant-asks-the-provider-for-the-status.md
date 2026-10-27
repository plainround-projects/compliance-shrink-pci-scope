# 2. The merchant asks the provider for the payment status

Status: accepted, 2026-10-27

## Context

After the card is confirmed, the browser returns to the merchant with `?payment_intent=pi_...`. That value comes from the customer's browser.

## Decision

`CheckoutService.complete` ignores everything the browser says except the token, rejects anything that is not a provider token, checks the order exists, and retrieves the intent from the provider with the secret key before recording a status. The webhook is the second path: it is applied only after its signature and timestamp verify, and repeating an event changes nothing. The price is fixed on the server.

## Alternatives considered

- **Trust a `status` parameter or the redirect.** Anyone could mark an order paid.
- **Webhook only.** Correct but the customer would wait for it; `done` asks once, the webhook confirms later.

## Consequences

- One more server-to-provider call per payment, with a timeout and retries.
- An event for an unknown payment is ignored, not an error.
