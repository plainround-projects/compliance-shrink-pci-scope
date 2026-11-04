# compliance-shrink-pci-scope

A checkout rebuilt so that card data never reaches the merchant: first the lesson's naive version (card details posted to your own server, whole form in the log), then a redesign where the browser sends the card straight to a payment provider's hosted fields and the merchant's server holds only tokens. A scope calculator draws the cardholder data environment before and after, a card-number scanner and a traffic capture prove nothing reaches the merchant's side, and an evidence pack ties each claim to a file a program produced.

| | |
| --- | --- |
| **Lesson** | `/prep/compliance/project-shrink-pci-scope`, "Shrink PCI scope by keeping card data out" (`data-structure-explainer/src/content/tracks/compliance/14-project-shrink-pci-scope.md` in the Plainround app) |
| **Planned hours** | 12 |
| **Level** | Advanced |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md), the scope inventories: [scope/](scope), the requirements: [controls/requirements.toml](controls/requirements.toml), decisions: [docs/adr](docs/adr) |

**Test mode only.** Everything uses the published test card `4242 4242 4242 4242` and test keys. The program refuses a live key (`sk_live_`, `pk_live_`). Never type a real card anywhere in this project.

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/architecture-dark.svg">
  <img alt="The customer browser sends the card straight to the payment provider's hosted fields, while the merchant's Token only web server, Charge component, order database and request log handle tokens. Prove it scans the merchant side and writes the evidence pack; the naive web server shows the before." src="docs/diagrams/architecture.svg">
</picture>

Notice that the card path bypasses the merchant boundary entirely, so only the provider is left holding card data.

## How one run flows

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/flow-dark.svg">
  <img alt="The run posts the test card to the naive app, whose log the scan finds holding it, then sends the card to the provider instead, so a repeat charge, a refund and the proof scan all see tokens only. The amber row is the scan finding the card in the naive log." src="docs/diagrams/flow.svg">
</picture>

The run ends with verify printing OK: 7 requirements, 14 files, 0 problem(s); the amber row is the before case that the redesign removes.

## Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| Python | 3.12 or 3.13 (tested with 3.13.12; the CI uses 3.12) | the apps, the scenario and the tests |
| GNU Make | 3.81 or newer | every command below |
| `grep` | any (BSD or GNU) | the lesson's own proof commands, run by the scenario |
| Docker | 24 or newer, optional | only for `docker compose up` (the scenario does not need it) |
| Python packages | `flask` 3.1 and `gunicorn` 23 at run time; pytest, pytest-cov, ruff, mypy, import-linter and pip-audit for development, all pinned with hashes in `requirements.lock` and `requirements-dev.lock`; `make` installs them into `.venv/` | everything |

No cloud account, no payment-provider account. **The provider is a local stand-in** (`pci_scope.interfaces.provider_app`) with the same shape of API as a real provider's test mode, so the lesson runs offline; see "What is simplified for teaching".

## Setup, run, test, stop

```bash
make up              # create .venv from the hash-pinned lock file and copy .env.example to .env
make run             # the scenario: naive checkout, redesign, proof, scope, evidence pack, verification
make test            # unit tests with coverage (domain and application at 95% or more)
make test-e2e        # the scenario as a test, against real local servers
make lint            # ruff, ruff format, mypy --strict, import-linter
make audit           # pip-audit over the locked dependencies
make check           # lint and test, what the CI runs first
make verify          # re-check the evidence pack in evidence/
make scope           # print the scope before and after
make scan PATHS="state evidence"   # search any folder for card numbers and card fields
make down            # delete state/ (nothing is running, so there is nothing to stop)
```

Run the three apps yourself in three terminals (`make serve-provider`, `make serve-merchant`, `make serve-naive`), or the first two as containers with `docker compose up --build` and open `http://127.0.0.1:5000`. `make run` starts its own copies on the ports in `.env` (5000, 5001, 5002), so stop any that are running first.

`make run` prints:

```text
scanning the naive checkout after one test payment:
  requests.log:1 FOUND card number 424242******4242
  requests.log:1 FOUND card field card_number
  requests.log:1 FOUND card field cvv
scanned 1 artifact(s): 3 findings
exit=1
scanning the merchant's side after the same payment, a repeat charge and a refund:
  merchant.db (SQL dump) ... clean
  backups/merchant-backup.sql ... clean
  merchant/app.log ... clean
scanned 3 artifact(s): 0 findings
exit=0
order statuses: {'pi_...': 'succeeded', 'pi_...': 'refunded'}
OK: 7 requirements, 14 files, 0 problem(s)
```

The numbers in the reports are masked (first six and last four digits), so a scan report never becomes another copy of the card.

## The SQL

| Script | What it is |
| --- | --- |
| [sql/001_schema.sql](sql/001_schema.sql) | DDL: the `orders` table. Every payment column is a provider token, and `GLOB` checks (`pi_*`, `cus_*`, `pm_*`) make a card number structurally impossible: the database itself refuses `4242424242424242` in a token column. |
| [sql/002_seed.sql](sql/002_seed.sql) | DML: two invented orders so the queries have rows. `make db` applies both. |
| [sql/003_queries.sql](sql/003_queries.sql) | The queries behind the proof: the table's columns, a search for card-shaped values, the tokens a repeat charge needs, revenue by status. `make queries` runs them. |

## Done when: the lesson's checklist and the proof for each line

| # | Done when (from the lesson) | Command | What proves it |
| --- | --- | --- | --- |
| 1 | The diagram shows the card number reaching your server, and lists the systems that are therefore in scope, including logs and the deploy pipeline. | `make scope`; `make run` | [evidence/scope-before.md](evidence/scope-before.md): a Mermaid diagram and a table of **9 systems and 3 teams**: web server, request log, log shipping, log search tool, order database, backups, developer laptops (all because card data reaches them), the CI/CD pipeline and the admin accounts (because they can change them). The "reaching your server" is shown for real in [evidence/proof-before.txt](evidence/proof-before.txt): after one test payment the naive checkout's log holds the number. The scope is computed from [scope/before.toml](scope/before.toml), not drawn by hand. |
| 2 | A test payment with the provider's test card succeeds, and your server's request logs and database contain a token, never a card number or CVV. | `make run`; `make test-e2e` | The scenario pays through the hosted fields: `order statuses: {... 'succeeded' ...}`. [evidence/token-storage.txt](evidence/token-storage.txt) shows the order table and its rows (`pi_...`, `cus_...`, `pm_...` only). The merchant's log lines read `created payment pi_... amount=1900 eur`. |
| 3 | No card number, CVV or full track data appears anywhere on your side, shown from the captured traffic and the logs. | `make run` | [evidence/payment.har](evidence/payment.har) and [payment-summary.txt](evidence/payment-summary.txt): `POST .../v1/payment_methods  card fields: card[cvc], card[exp_month], card[exp_year], card[number]  -> the provider`; every request to `your server` has `body: (empty)` or no card fields. [evidence/proof-after.txt](evidence/proof-after.txt): the scanner reads the log, the database (as SQL text) and the backup, 0 findings, and the lesson's two `grep` commands exit 1 (nothing found). `verify` recomputes the claim from the raw HAR, not from the summary. |
| 4 | A repeat charge works from the stored token alone, and the README explains why a token is safer to hold than a card number. | `make run` | The scenario calls `/charge-again` on the first order: the merchant sends the provider only `customer` and `payment_method` tokens and the second payment succeeds; a refund then uses only the payment token. **Why a token is safer:** a token is meaningful only to the account that holds it at the provider, so a thief who steals the order table cannot spend it anywhere else; a card number can be used anywhere, which is why holding one brings the whole of PCI scope. Treat tokens as sensitive anyway (stored encrypted, kept out of logs). |
| 5 | The after-diagram shows card data flowing only between the browser and the provider, and the list names systems removed from scope. | `make scope`; `make run` | [evidence/scope-after.md](evidence/scope-after.md): the only data edge into anything is `browser -> provider`. [evidence/scope-change.md](evidence/scope-change.md): 9 systems and 3 teams become **3 systems and 2 teams**; left scope: request log, log shipping, log search tool, order database, backups, developer laptops; still in scope: the web server (it serves the page that loads the provider's script), the pipeline that deploys it and the admin accounts that can change it. |
| 6 | The evidence pack would support a reduced-scope assessment, and it names what you still must do even with tokenization. | `make verify` | [evidence/INDEX.md](evidence/INDEX.md) maps seven requirements to fourteen files; `manifest.json` records each file's hash, so a hand edit fails `verify` (EVP003). [evidence/responsibilities.md](evidence/responsibilities.md) lists what is now the provider's and what is still ours (the payment page and its pipeline, the content security policy, no logging of bodies, the provider's attestation and contract, the questionnaire for the merchant level). [evidence/checkout-page-controls.txt](evidence/checkout-page-controls.txt) shows the policy and the inventory of scripts and frames the page loads. **One gap is tracked, not hidden:** the provider's attestation of compliance (P7, ticket PCI-1), because the stand-in has none. |

### What the checks catch

`pci-scope verify` (and the unit tests) fail when: a card field or number appears in a request to the merchant in the HAR (EVP007); the merchant-side scan has findings or covers fewer than three artifacts; `POST /pay` or `GET /pay` answers anything but 404; the scope did not shrink; a file is missing, empty, edited by hand or unclaimed (EVP002 to EVP004); a requirement has no evidence and no tracked gap (EVP001).

## Stretch goals

| Stretch (from the lesson) | Built? |
| --- | --- |
| Add a webhook from the provider for the final payment result and verify its signature. | Yes. The provider signs each event (`t=<time>,v1=<HMAC-SHA256>` over `<time>.<body>`); the merchant's `/webhook` verifies the signature and a five-minute window before touching an order; repeating an event changes nothing. Tested for a missing, forged, tampered and old signature. |
| Handle a refund through the provider using the token and show no card data is needed. | Yes. `/refund` sends only the payment-intent token; the scenario refunds the repeat charge and the order becomes `refunded`. |
| List the provider's own attestation you would collect as part of third-party risk. | Yes. [docs/provider-attestation.md](docs/provider-attestation.md) lists what to collect (the attestation of compliance for service providers, its date, the services covered, the integration type) and is the tracked gap P7. |

## What is simplified for teaching

- **The provider is a local stand-in, not any real provider.** It implements the subset of a payment-intents style REST API that the lesson uses (customers, payment intents, payment methods, confirm, refunds, signed webhooks) plus a hosted card form. The merchant's `HttpProvider` speaks that shape, so pointing `PROVIDER_BASE_URL` and the keys at a real provider's test mode is the intended next step; **it has not been run against a real provider**, because there is no account here. The stand-in keeps only the last four digits of a card and its state is in memory.
- **The browser is scripted.** `Browser` (in `interfaces/browser_sim.py`) makes the requests the page's JavaScript makes (load the provider's script, create the payment, load the card frame, send the card to the provider, confirm, return) over real HTTP, and records them as a HAR. It does not execute JavaScript. The two small scripts (`checkout.js` and the provider's `elements.js`) are not covered by an automated browser test. They were run once by hand in a real browser (the Claude desktop app's built-in browser) against `make serve-provider` and `make serve-merchant`: the provider's iframe mounted, the published test card was typed into it, Pay returned to `/done` with `payment pi_...: succeeded`, and a scan of the merchant's log and database found nothing (0 findings).
- The scope is computed from two inventories (`scope/*.toml`), which describe a typical small setup; a real assessment starts from the real network and the real people.
- Card-number detection is the Luhn check on 13 to 19 digits, which can flag a long numeric id that happens to pass it. A false positive is acceptable in a scan whose cost is a look at one line; allow-listing is the production answer.
- The "backups" are one SQL dump taken after the payments; the log "shipping" and "search tool" exist only in the inventory.

## Project structure

```text
src/pci_scope/
  domain/            card (Luhn, masking, the scan), scope (the computation and its reports), webhook (signing),
                     har (the capture and its checks), evidence (the pack rules), payment (tokens, orders), findings.
                     Depends on the standard library only.
  application/       CheckoutService (start, complete, charge again, refund, webhook), the scan use case, the pack
                     text, and the ports (PaymentProvider, OrderRepository, ArtifactReader, EvidenceStore).
                     Depends on domain only.
  infrastructure/    HttpProvider (urllib, timeouts, retries), SQLite orders, artifact readers, the evidence folder,
                     the TOML catalogs, settings, JSON logging. Depends on application and domain.
  interfaces/        the provider stand-in, the merchant, the naive app (Flask), the scripted browser, the local
                     servers, the demo scenario, the gunicorn factories and the pci-scope command line. Nothing depends on it.
scope/               before.toml and after.toml: the systems and how they connect.
controls/            requirements.toml: each requirement, its evidence, and the tracked gap.
sql/                 001_schema, 002_seed, 003_queries.
docs/                responsibilities.md, provider-attestation.md (copied into the pack), adr/.
evidence/            the pack that `make run` produced (a sample; it is rewritten on every run).
tests/
  unit/              domain, application (fake provider and orders), infrastructure, the apps over Flask's test client.
  e2e/               the scenario against real local servers.
Dockerfile, docker-compose.yml   the provider and the merchant as containers (non-root, read-only, pinned base image).
tech/                56 beginner notes, one per technology, with every source file quoted and explained line by line; start at tech/README.md.
pyproject.toml       metadata and every tool's configuration.   requirements*.lock  hash-pinned dependencies.
Makefile             the only commands a reader needs.          .github/workflows/ci.yml  the same checks on push.
```

The dependency rule (domain depends on nothing; application on domain; infrastructure and interfaces on both; nothing on interfaces) is enforced by `make lint` through import-linter, and a second contract forbids `domain` and `application` from importing Flask or SQLite.

## Verification status of the tech/ notes

The notes in `tech/` were checked against the repository: every quoted line comes from a file here, and every command that needs no container was run and its output compared. The commands that build or start containers were written while the host had no capacity (load average above 300, swap nearly full), so they were not run. pending capacity: run `docker build -t compliance-shrink-pci-scope:dev .` and `docker compose up --build`, then the container commands in [tech/docker.md](tech/docker.md), [tech/dockerfile.md](tech/dockerfile.md) and [tech/docker-compose.md](tech/docker-compose.md), compare their output with what each note says, then `docker compose down -v`. The note [tech/env-files.md](tech/env-files.md) describes the variables from `settings.py` and `docker-compose.yml` only, because `.env.example` could not be read by the tool that wrote the notes (its permission settings deny reading it).

## Author and license

Written by Sumit Srivastava. Released under the MIT License, see [LICENSE](LICENSE). Changes are in [CHANGELOG.md](CHANGELOG.md).
