# HAR (HTTP Archive)

## What it is

HAR (HTTP Archive) is a JSON format for recording web traffic: a list of **entries**, each with a request (method, URL, body) and the
response (status). Browsers' developer tools can export one. It is how you show who received what.

## Why this repository uses it

The lesson asks for proof "from the captured traffic" that no card number reaches your side. The scripted browser records every request, the
program writes them as a HAR, and the check reads the HAR back to confirm that no request to the merchant carries card data.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/domain/har.py` | `to_har`, `parse_har`, `summarize`, `merchant_exposure`, `reaches_provider`. |
| `evidence/payment.har` | The capture. |
| `evidence/payment-summary.txt` | The same capture, one line per request. |
| `src/pci_scope/domain/evidence.py` | `verify_pack` re-reads the HAR. |

## How it works underneath

A HAR file is `{"log": {"version": "1.2", "creator": {...}, "entries": [...]}}`. Each entry has `request.method`, `request.url`,
`request.postData.text` and `response.status`. This project writes the minimum it needs. Bodies sent to the **provider** keep their field
names but lose the values (`card[number]=[redacted]`), so the capture shows where the card fields went **without becoming a new copy of the card**.

## Walkthrough of this repository's use

`src/pci_scope/domain/har.py`:

```python
def to_har(exchanges: list[Exchange], redact_for: frozenset[str]) -> str:
    """HAR 1.2. Bodies sent to an origin in `redact_for` (the provider) keep their field names and lose the values, so
    the capture shows where the card fields went without becoming a new copy of the card."""
    entries = []
    for item in exchanges:
        body = item.body
        if origin(item.url) in redact_for and body:
            body = "&".join(f"{pair.split('=', 1)[0]}=[redacted]" for pair in body.split("&"))
        entries.append(
            {
                "request": {"method": item.method, "url": item.url, "postData": {"text": body}},
                "response": {"status": item.status},
            }
        )
    return (
        json.dumps(
            {
                "log": {
                    "version": "1.2",
                    "creator": {"name": "pci-scope browser simulator", "version": "0.1"},
                    "entries": entries,
                }
            },
            indent=2,
        )
        + "\n"
```

- For each request to an origin in `redact_for` (the provider), the body is rewritten to keep the names and hide the values.
- The entries are built as dictionaries and written with `json.dumps(..., indent=2)`.

`src/pci_scope/domain/har.py`:

```python
def merchant_exposure(exchanges: list[Exchange], merchant: str) -> list[str]:
    """Problems: any request to the merchant whose body or URL holds a card field or a card number."""
    problems = []
    for item in exchanges:
        if origin(item.url) != merchant:
            continue
        text = f"{item.url}\n{item.body}"
        if card_field_names(text) or scan_text("har", text):
            problems.append(f"{item.method} {item.url} carries card data")
    return problems
```

The check: for any request whose origin is the merchant, search the URL and body for a card field name or a Luhn-valid number. Any hit is a
problem. An empty list is the proof.

`src/pci_scope/domain/har.py`:

```python
def reaches_provider(exchanges: list[Exchange], provider: str) -> bool:
    """True when at least one request to the provider carries the card fields (the card went where it should)."""
    return any(origin(item.url) == provider and card_field_names(item.body) for item in exchanges)
```

The second half of the proof: the card fields **did** go somewhere, and that somewhere is the provider. Without it, "no card data reaches us" could be true because
the test never sent a card at all.

## Try it yourself

```bash
.venv/bin/python -c "import json; d = json.load(open('evidence/payment.har')); print(d['log']['version'], len(d['log']['entries']))"
```
Prints `1.2 8`.

```bash
grep -n "redacted" evidence/payment.har | head -2
```
Shows the provider-bound body with the values replaced.

```bash
.venv/bin/python - <<'EOF'
from pci_scope.domain.har import parse_har, merchant_exposure, reaches_provider
ex = parse_har(open("evidence/payment.har").read())
print(merchant_exposure(ex, "http://127.0.0.1:5000"), reaches_provider(ex, "http://127.0.0.1:5001"))
EOF
```
Prints `[] True`: nothing reached the merchant; the card fields reached the provider.

```bash
cat evidence/payment-summary.txt | head -4
```
Shows the human-readable summary.

## Mistakes people make

- **Saving a real HAR with real card data** into a repository. This one is redacted for the provider and uses the test card.
- **Proving only the negative.** `reaches_provider` shows the card went to the right place.
- **Checking only bodies.** URLs are searched too.
- **Trusting a HAR that was edited.** It is in the manifest; a hand edit fails `make verify`.

## Check yourself

1. What does a HAR entry contain?
   **Answer:** A request (method, URL, body) and a response (status).
2. Why are provider-bound values redacted?
   **Answer:** So the capture is not a new copy of the card.
3. Why does the check also require that the card reached the provider?
   **Answer:** Otherwise the test could pass without ever sending a card.
4. Where is the HAR protected against edits?
   **Answer:** The manifest's SHA-256 for `payment.har`.
5. What does `merchant_exposure` return when all is well?
   **Answer:** An empty list.

## Further reading

- HAR 1.2 specification (community draft): <http://www.softwareishard.com/blog/har-12-spec/>
- Chrome DevTools, network features: <https://developer.chrome.com/docs/devtools/network/>
