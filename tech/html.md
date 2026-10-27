# HTML

## What it is

HTML (HyperText Markup Language) is the language of web pages. A page is made of **elements** written as tags: `<h1>Title</h1>`,
`<button>`, `<form>`, `<input>`. Tags can have **attributes** (`name="card_number"`). A browser reads the HTML and draws the page; a `<form>` sends its
inputs to the server when submitted; a `<script>` runs code; an `<iframe>` embeds another page.

## Why this repository uses it

The difference between the naive and the redesigned checkout is visible in the HTML. In the naive page the card fields are inputs of a form
that posts to the merchant. In the redesigned page there are no card inputs at all: an empty `<div id="card">` is filled by the
provider's script with an `<iframe>` served by the provider.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/naive_app.py` | `FORM`: card number, expiry and CVV in a form that posts to `/pay`. |
| `src/pci_scope/interfaces/merchant_app.py` | `PAGE`: the redesigned page without card inputs. |
| `src/pci_scope/interfaces/provider_app.py` | `FRAME_HTML`: the card form, inside the provider's iframe. |

## How it works underneath

The browser parses the HTML into a tree (the **DOM**). Each `<script src="...">` makes the browser fetch and run that file. An
`<iframe src="...">` loads another page in a box; because it comes from another **origin**, the outer page cannot read what is typed in it.
That separation is the whole idea of hosted fields.

## Walkthrough of this repository's use

`src/pci_scope/interfaces/naive_app.py`:

```python
FORM = """<form method="post" action="/pay">
  Card <input name="card_number"> Expiry <input name="expiry"> CVV <input name="cvv">
  <button>Pay 19.00</button></form>"""
```

**Before.** `<form method="post" action="/pay">` sends the three inputs (`card_number`, `expiry`, `cvv`) to the merchant's own `/pay` when the
button is pressed.

`src/pci_scope/interfaces/merchant_app.py`:

```python
PAGE = """\
<!doctype html>
<meta charset="utf-8">
<title>Checkout</title>
<h1>Pay 19.00 EUR</h1>
<div id="card"></div>
<button id="pay" type="button">Pay 19.00</button>
<p id="message" role="status"></p>
<script src="__PROVIDER__/v1/elements.js"></script>
<script src="/static/checkout.js" data-key="__KEY__"></script>
"""
```

**After.** The page has a heading, an empty `<div id="card"></div>` where the card form will appear, a button, a status line
(`role="status"` for screen readers), and two scripts: the provider's (`__PROVIDER__/v1/elements.js`) and the merchant's
(`/static/checkout.js`, with the publishable key in a `data-key` attribute). `__PROVIDER__` and `__KEY__` are placeholders the app replaces
with `str.replace`. `<!doctype html>` and `<meta charset="utf-8">` set the mode and the text encoding.

`src/pci_scope/interfaces/provider_app.py`:

```python
FRAME_HTML = """\
<!doctype html>
<meta charset="utf-8">
<title>Card details</title>
<form id="card" autocomplete="off">
  <label>Card number <input id="number" inputmode="numeric" autocomplete="cc-number"></label>
  <label>Expiry <input id="expiry" placeholder="MM / YY" autocomplete="cc-exp"></label>
  <label>CVC <input id="cvc" inputmode="numeric" autocomplete="cc-csc"></label>
</form>
<script>
```

The provider's frame holds the three card inputs. `autocomplete="cc-number"` and friends let the browser offer saved cards;
`inputmode="numeric"` shows a number keyboard on phones; `autocomplete="off"` on the form keeps the browser from storing the entries.

## Try it yourself

```bash
.venv/bin/python -c "from pci_scope.interfaces.naive_app import FORM; print(FORM)"
```
Prints the naive form with the three card inputs.

```bash
.venv/bin/python -c "from pci_scope.interfaces.merchant_app import PAGE; print('card_number' in PAGE, 'cvv' in PAGE, PAGE.count('<script'))"
```
Prints `False False 2`: no card inputs on the redesigned page; two scripts.

```bash
.venv/bin/python -c "from pci_scope.domain.card import card_field_names; from pci_scope.interfaces.merchant_app import PAGE; from pci_scope.interfaces.naive_app import FORM; print(card_field_names(FORM), card_field_names(PAGE))"
```
Prints `['card_number', 'cvv']` for the naive form and `[]` for the new page: the same detector the evidence uses.

```bash
cat evidence/payment-summary.txt | head -3
```
Shows that loading the page sends no card fields anywhere.

## Mistakes people make

- **A card input on the merchant's own page**, even "temporarily", which puts the page and server back in scope.
- **Loading scripts from many places.** Every script on the payment page can read it; the policy lists two origins.
- **Forgetting `autocomplete` hints**, which makes card entry harder for customers.
- **Pasting user input into HTML** without escaping (cross-site scripting). The page here contains only fixed text and two values the app controls.

## Check yourself

1. What does `<form method="post" action="/pay">` do?
   **Answer:** Sends the inputs to `/pay` on the same server when submitted.
2. Why is the redesigned page free of card inputs?
   **Answer:** The provider's iframe shows them, so the card never reaches the merchant.
3. What is an iframe?
   **Answer:** A page embedded in another page; from another origin it is isolated.
4. What does `role="status"` do?
   **Answer:** Tells assistive technology that the element shows status messages.
5. How does the app fill `__PROVIDER__`?
   **Answer:** With `str.replace` before sending the page.

## Further reading

- MDN, HTML elements: <https://developer.mozilla.org/en-US/docs/Web/HTML/Element>
- HTML Living Standard: <https://html.spec.whatwg.org/multipage/>
