# Evidence pack index

Pack date: 2026-10-27T01:24:50Z. Every file was produced by `make run` (`pci-scope demo`); `manifest.json` records its hash, so a hand edit fails `make verify`.

| File | Requirement | Proves | Date |
| --- | --- | --- | --- |
| payment.har | P1 | the captured browser traffic: no request to the merchant carries a card field or number, and the card fields went to the provider | 2026-10-27 |
| payment-summary.txt | P1 | the same capture, one line per request with where it went | 2026-10-27 |
| proof-after.txt | P1 | a scan of the merchant's log, database and backups for card numbers and card fields, and the lesson's grep commands, all empty | 2026-10-27 |
| route-check.txt | P2 | POST and GET /pay on the merchant answer 404 | 2026-10-27 |
| scope-before.md | P3 | the cardholder data environment of the naive checkout: 9 systems and 3 teams | 2026-10-27 |
| scope-after.md | P3 | the cardholder data environment after the redesign | 2026-10-27 |
| scope-change.md | P3 | what left scope and what stays | 2026-10-27 |
| proof-before.txt | P4 | the same scan, run on the naive checkout after one test payment, finds the number | 2026-10-27 |
| token-storage.txt | P5 | the order table's columns, sample rows holding only pi_, cus_ and pm_ tokens, and the check for card-number columns | 2026-10-27 |
| checkout-page-controls.txt | P6 | the content security policy of the payment page and the inventory of the scripts and frames it loads | 2026-10-27 |
| responsibilities.md | P6 | what is now the provider's and what is still the merchant's | 2026-10-27 |
| provider-attestation.md | P7 | the record of the provider's attestation of compliance, its date and the services it covers | 2026-10-27 |

## Tracked gaps

- P7: This build uses a local stand-in for the provider, which has no attestation. With a real provider, download its attestation of compliance, record its date and services here, and close this gap. Ticket PCI-1, due 2026-12-01.

## What the merchant still does

See `responsibilities.md`: the payment page and its pipeline, the content security policy, no logging of bodies, the provider's attestation, the questionnaire for the merchant level.
