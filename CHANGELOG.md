# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-27

### Added

- The lesson's naive checkout, kept to be measured, and the redesigned merchant: a payment page with no card field and a content security policy that names only the provider, `create-payment`, `done`, `charge-again`, `refund` and a signed `webhook`; there is no route that accepts a card.
- A local payment-provider stand-in with a payment-intents style API, a hosted card form served from its own origin, test cards, off-session charges, refunds and signed webhooks.
- A scope calculator over two inventories (9 systems and 3 teams before, 3 and 2 after), a Luhn-based card-number scanner with masked evidence, a scripted browser that records a HAR, and a verification of the evidence pack that recomputes the claims from the raw capture.
- SQL scripts: an order table whose token columns reject card numbers, sample rows and the proof queries.
- Layered package with the dependency rule enforced by import-linter, unit tests, an end-to-end scenario, ruff, mypy strict, hash-pinned lock files, a Dockerfile and compose file, and a CI workflow.
