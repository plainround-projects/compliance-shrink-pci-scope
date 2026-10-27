# 1. A local stand-in for the payment provider

Status: accepted, 2026-10-27

## Context

The lesson uses a provider's hosted fields in test mode. That needs an account, keys and a network, and a repository that cannot run without them cannot be verified offline or in a fresh clone.

## Decision

Implement the provider's side locally, with the same shape as a typical payment-intents API: customers, payment intents with a client secret, payment methods created from the browser with a publishable key, confirm, off-session charges, refunds and signed webhooks, plus a hosted card form served from the provider's origin. The merchant's `HttpProvider` speaks only that API, configured by `PROVIDER_BASE_URL` and test keys; settings refuse live keys.

## Alternatives considered

- **Call a real provider's test mode.** The intended use; not possible here without an account, and it makes the tests depend on the network and on the provider's changes.
- **Mock the provider inside the tests only.** Then `make run` would show nothing and the traffic capture would be invented.
- **A recorded-response library.** Replays answers but cannot serve the iframe or the script, so the page and the capture would not be real.

## Consequences

- The scenario, the capture and the tests are real HTTP between three servers, repeatable offline.
- The provider side is not a real provider; the README names it and the next step (point the variables at a real test mode).
- The provider's attestation of compliance cannot exist for a stand-in, so requirement P7 is a tracked gap.
