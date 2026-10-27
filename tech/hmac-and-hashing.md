# HMAC-SHA256, SHA-256 and secrets

## What it is

A **hash** (SHA-256) turns any text into a fixed 64-character fingerprint; the same input always gives the same fingerprint and you cannot go
back. An **HMAC** mixes a **secret key** into the hash, so only the key's holder can produce it. A **webhook** is an HTTP request that one
system sends to another when something happens (here: the provider tells the merchant a payment succeeded). Anyone could POST to the
merchant's `/webhook` address, so the merchant must check a **signature**.

## Why this repository uses it

The merchant does not take the browser's word that a payment worked; it asks the provider, and it also listens for the provider's
signed events. A forged "payment succeeded" must be refused, an old signed event must not be replayed, and the evidence files must be
protected against hand edits.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/domain/webhook.py` | `sign` and `verify`. |
| `src/pci_scope/application/checkout.py` | `handle_event` verifies before acting. |
| `src/pci_scope/interfaces/provider_app.py` | Signs each event it emits. |
| `src/pci_scope/domain/evidence.py` | `digest(text)`: the SHA-256 recorded in the manifest. |
| `src/pci_scope/infrastructure/settings.py` | `WEBHOOK_SECRET` must be at least 32 characters. |

## How it works underneath

`hmac.new(key, message, hashlib.sha256).hexdigest()` computes the keyed fingerprint. The provider signs `<timestamp>.<body>`, and sends
`t=<timestamp>,v1=<signature>`. The merchant recomputes the signature from the received body with its own copy of the secret and
compares with `hmac.compare_digest` (constant time, so timing leaks nothing). Including the **timestamp** in the signed text lets the
merchant refuse an event that is too old or too new (a **replay**).

## Walkthrough of this repository's use

`src/pci_scope/domain/webhook.py`:

```python
def sign(secret: str, body: bytes, timestamp: int) -> str:
    """The header value `t=<timestamp>,v1=<hex hmac>` over `<timestamp>.<body>`."""
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"
```

`f"{timestamp}.".encode() + body` is the signed message: the timestamp, a dot, then the exact body bytes. The header carries the
timestamp and the signature.

`src/pci_scope/domain/webhook.py`:

```python
def verify(secret: str, body: bytes, header: str | None, now: int, tolerance: int = TOLERANCE_SECONDS) -> bool:
    """True only for a signature made with the secret, over this body, no older (or newer) than the tolerance."""
    if not header:
        return False
    parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
    if not parts.get("t", "").isdigit() or "v1" not in parts:
        return False
    timestamp = int(parts["t"])
    expected = sign(secret, body, timestamp).split("v1=", 1)[1]
    return hmac.compare_digest(parts["v1"], expected) and abs(now - timestamp) <= tolerance
```

- No header, a header without `t` or `v1`, or a non-numeric timestamp: refuse.
- Otherwise recompute the expected signature and `hmac.compare_digest` it, **and** require `abs(now - timestamp) <= tolerance` (300
  seconds). Both must hold.

`src/pci_scope/application/checkout.py`:

```python
    def handle_event(self, body: bytes, signature: str | None, now: int) -> str:
        """Apply a provider event after checking its signature. Repeating an event changes nothing."""
        if not verify(self._webhook_secret, body, signature, now):
            raise PaymentError("webhook signature is not valid")
        event = json.loads(body)
        intent = event["data"]["object"]
        order = self._orders.find(intent["id"])
```

Nothing in the event is trusted until the signature verifies. Repeating an event changes nothing (the status is set, not added to).

`src/pci_scope/domain/evidence.py`:

```python
def digest(text: str) -> str:
    """SHA-256 of a file's text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
```

The manifest records this SHA-256 for each evidence file; `make verify` recomputes it, so an edited file is caught.

## Try it yourself

```bash
.venv/bin/python - <<'EOF'
from pci_scope.domain.webhook import sign, verify
secret, body = "s" * 32, b'{"type":"payment_intent.succeeded"}'
header = sign(secret, body, 1_000_000)
print(header[:13])
print(verify(secret, body, header, 1_000_100))      # inside the tolerance
print(verify(secret, body + b" ", header, 1_000_100))  # body changed
print(verify("x" * 32, body, header, 1_000_100))    # wrong secret
print(verify(secret, body, header, 1_002_000))      # too old
print(verify(secret, body, None, 1_000_100))        # no header
EOF
```
Prints `t=1000000,v1=` then `True False False False False`.

```bash
.venv/bin/python -c "import hashlib; print(hashlib.sha256(b'abc').hexdigest())"
```
Prints `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`.

```bash
.venv/bin/python -c "import json, hashlib; m = json.load(open('evidence/manifest.json')); t = open('evidence/route-check.txt').read(); print(hashlib.sha256(t.encode()).hexdigest() == m['route-check.txt']['sha256'])"
```
Prints `True`: the file still matches its manifest entry.

```bash
.venv/bin/pytest -q -k webhook tests/unit
```
Runs the webhook tests.

## Mistakes people make

- **Accepting a webhook without checking the signature.** Anyone can POST to it.
- **Signing without a timestamp**, which lets an attacker replay an old valid event.
- **Verifying a re-serialized body.** The check uses the exact bytes received.
- **Comparing signatures with `==`.** Use `hmac.compare_digest`.
- **A short secret.** The settings loader refuses under 32 characters.

## Check yourself

1. Why include a timestamp in the signed text?
   **Answer:** So an old, valid event cannot be replayed later.
2. What does `hmac.compare_digest` avoid?
   **Answer:** Timing differences that could reveal how much of a secret matched.
3. What happens to a webhook with a wrong signature?
   **Answer:** `PaymentError`; the merchant answers `402` and changes nothing.
4. What is signed?
   **Answer:** `<timestamp>.<body>`, the exact bytes received.
5. What does the manifest's `sha256` protect?
   **Answer:** The evidence file against hand edits.

## Further reading

- `hmac` (Python 3.12): <https://docs.python.org/3.12/library/hmac.html>; `hashlib`: <https://docs.python.org/3.12/library/hashlib.html>
- HMAC (RFC 2104): <https://www.rfc-editor.org/rfc/rfc2104>
