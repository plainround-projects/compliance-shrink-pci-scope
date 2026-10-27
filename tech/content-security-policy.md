# Content-Security-Policy and the other security headers

## What it is

A **Content-Security-Policy (CSP)** is an HTTP response header with which a site tells the browser where it may load things from. If a
script tries to load from somewhere not on the list, the browser refuses. Other small headers add protection too:
`X-Content-Type-Options: nosniff`, `Referrer-Policy` and `Cache-Control`.

## Why this repository uses it

Once the merchant's page loads the provider's script, anything that can change that page can steal what the customer types (this is how
card-skimming attacks work). The policy shrinks what the page may load to the merchant itself and the provider, and the evidence file
`checkout-page-controls.txt` records it. The requirements that still apply to the merchant's payment page are part of the smaller scope.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/merchant_app.py` | The `Content-Security-Policy` and three other headers on every response. |
| `src/pci_scope/interfaces/provider_app.py` | The card frame's own policy (`frame-ancestors`). |
| `evidence/checkout-page-controls.txt` | The captured headers. |

## How it works underneath

The browser reads the header and applies each **directive** as a rule. `default-src 'self'` means "everything may come from my own
origin". `script-src 'self' <provider>` adds the provider for scripts. `frame-src <provider>` lets the page embed the provider's frame.
`connect-src 'self'` limits `fetch` calls to the same origin. `form-action 'self'` stops a form from being posted elsewhere.
`base-uri 'none'` forbids a `<base>` tag. `frame-ancestors 'none'` forbids anyone from embedding this page.

## Walkthrough of this repository's use

`src/pci_scope/interfaces/merchant_app.py`:

```python
    policy = (
        f"default-src 'self'; script-src 'self' {provider_base_url}; frame-src {provider_base_url}; "
        f"connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    )
```

The policy is built with the provider's address: scripts from the merchant and the provider only, frames from the provider only, `fetch` to
the merchant only, forms to the merchant only, no `<base>`, and the page may not be framed by others.

`src/pci_scope/interfaces/merchant_app.py`:

```python
    @app.after_request
    def secure(response: Response) -> Response:
        response.headers["Content-Security-Policy"] = policy
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response
```

The header is added to every response by the `after_request` hook, together with `nosniff` (the browser must not guess a file's type),
`Referrer-Policy: no-referrer` (do not tell other sites where the user came from) and `Cache-Control: no-store` (do not keep the page).

`src/pci_scope/interfaces/provider_app.py`:

```python
        response.headers["Content-Security-Policy"] = (
            f"frame-ancestors {origin or 'none'}; default-src 'self'; script-src 'self' 'unsafe-inline'"
        )
```

The provider's frame allows only the merchant's origin to embed it: `frame-ancestors <origin>`.

## Try it yourself

```bash
cat evidence/checkout-page-controls.txt
```
Shows the response headers captured from the merchant's page.

```bash
.venv/bin/python - <<'EOF'
from pci_scope.interfaces.merchant_app import create_merchant_app
app = create_merchant_app(None, "http://127.0.0.1:5001", "pk_test_x")
r = app.test_client().get("/healthz")
print(r.headers["Content-Security-Policy"])
print(r.headers["X-Content-Type-Options"], r.headers["Cache-Control"])
EOF
```
Prints the policy (with `script-src 'self' http://127.0.0.1:5001`) and `nosniff no-store`.

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output follows from the files quoted above and from the README's verified runs.

```bash
curl -sI http://127.0.0.1:5000/ | grep -i "content-security-policy"
```
With the merchant running, prints the same header over HTTP.

## Mistakes people make

- **`'unsafe-inline'` in the merchant's `script-src`.** The merchant's script is a separate file for that reason (the provider's frame needs
  it for its own tiny script, which is served from the provider).
- **Listing a CDN "just in case".** Every origin on the list is code that can read the page.
- **Thinking a CSP replaces the other controls.** It reduces risk; the requirements for the payment page still apply.
- **Forgetting that a header on one route is not on the others.** The `after_request` hook covers all of them.

## Check yourself

1. What does `default-src 'self'` mean?
   **Answer:** Anything not covered by a more specific directive may load only from the page's own origin.
2. What does `frame-ancestors 'none'` stop?
   **Answer:** Other sites embedding this page.
3. Why does the merchant name the provider in `script-src`?
   **Answer:** Its page loads the provider's script.
4. What does `nosniff` do?
   **Answer:** Tells the browser to trust the declared content type and not guess.
5. Why add the headers in `after_request`?
   **Answer:** So every response gets them.

## Further reading

- MDN, Content-Security-Policy: <https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP>
- CSP Level 3: <https://www.w3.org/TR/CSP3/>
