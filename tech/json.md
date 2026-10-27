# JSON

## What it is

JSON (JavaScript Object Notation) is a text format for data made of objects (`{"key": value}`), arrays (`[1, 2]`), text in double
quotes, numbers, `true`, `false` and `null`. `json.dumps` turns Python values into JSON text; `json.loads` turns it back.

## Why this repository uses it

JSON is the language of the provider's API answers, of webhook events, of the browser capture (HAR is JSON) and of the manifest that
records each evidence file's hash. The logs are JSON lines too, with only whitelisted fields.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/provider_app.py` | `jsonify` for every answer; `json.dumps(event)` for webhooks. |
| `src/pci_scope/infrastructure/provider_http.py` | `json.loads(response.read())` for provider answers. |
| `src/pci_scope/domain/har.py` | Writes and reads the HAR file. |
| `src/pci_scope/infrastructure/evidence_store.py` | `manifest.json`. |
| `src/pci_scope/infrastructure/logging_setup.py` | One JSON object per log line. |

## How it works underneath

JSON text is parsed into Python `dict`, `list`, `str`, `int`, `float`, `bool` and `None`. `sort_keys=True` writes keys in a fixed
order, so the same data always gives the same text and the same hash. `indent=2` adds line breaks for people.

## Walkthrough of this repository's use

`src/pci_scope/infrastructure/provider_http.py`:

```python
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    return dict(json.loads(response.read()))
```

`json.loads(response.read())` parses the provider's answer; `dict(...)` makes sure it is a dictionary.

`src/pci_scope/infrastructure/provider_http.py`:

```python
def _message(problem: urllib.error.HTTPError) -> str:
    try:
        return str(json.loads(problem.read())["error"]["message"])
    except (ValueError, KeyError, TypeError):
        return f"the provider refused the request ({problem.code})"
```

A provider error looks like `{"error": {"message": "..."}}`. The function digs the message out, and if the body is not JSON or the
keys are missing (`ValueError`, `KeyError`, `TypeError`) it falls back to a generic message with the status code.

`src/pci_scope/interfaces/provider_app.py`:

```python
    def emit(kind: str, intent: dict[str, Any]) -> None:
        event = {"id": _id("evt"), "type": kind, "data": {"object": _public(intent)}}
        state.events.append(event)
        body = json.dumps(event).encode()
```

A webhook event is a dictionary turned into **bytes** with `json.dumps(event).encode()`; the same bytes are signed and sent (see
`hmac-and-hashing.md`), so the receiver verifies exactly what it received.

`src/pci_scope/infrastructure/evidence_store.py`:

```python
        entries[name] = {
            "requirement": requirement,
            "produced_at": produced_at.astimezone(UTC).strftime(_TIME),
            "sha256": digest(text),
        }
        self._path(MANIFEST).write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

The manifest is JSON keyed by file name; it is written with `json.dumps(entries, indent=2, sort_keys=True) + "\n"`. See `har.md` for
the capture.

## Try it yourself

```bash
head -12 evidence/manifest.json
```
Shows the first manifest entries: `requirement`, `produced_at`, `sha256`.

```bash
.venv/bin/python -m json.tool evidence/payment.har | head -12
```
Pretty-prints the HAR capture with Python's built-in tool.

```bash
.venv/bin/python -c "import json; print(json.dumps({'b': 1, 'a': [None, True]}, sort_keys=True), json.loads('[1, 2, 3]'))"
```
Prints `{"a": [null, true], "b": 1} [1, 2, 3]`.

```bash
.venv/bin/python -c "import json; json.loads('{bad')" 2>&1 | tail -1
```
Prints `json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: ...`.

## Mistakes people make

- **Single quotes or trailing commas** in JSON.
- **Signing a different serialization** than the one sent. The same bytes are signed and sent.
- **Putting secrets or card data in logs.** Only whitelisted fields are written.
- **Assuming a provider answer is always JSON.** `_message` handles a body that is not.

## Check yourself

1. What does `sort_keys=True` buy?
   **Answer:** The same data always gives the same text, so the same hash.
2. Why are webhook bytes created once and signed and sent as they are?
   **Answer:** The receiver must verify exactly what it received.
3. What does `json.loads` raise for invalid JSON?
   **Answer:** `json.JSONDecodeError`, a kind of `ValueError`.
4. What is HAR?
   **Answer:** A JSON format for recorded web traffic (see `har.md`).
5. Why are log fields whitelisted?
   **Answer:** So nothing unexpected, such as card data, can end up in a log line.

## Further reading

- `json` (Python 3.12): <https://docs.python.org/3.12/library/json.html>
- JSON (RFC 8259): <https://www.rfc-editor.org/rfc/rfc8259>
