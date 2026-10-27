# JavaScript (the two small browser scripts)

## What it is

JavaScript is the language browsers run inside web pages. A script can read and change the page (the **DOM**), make network
requests with `fetch`, react to clicks, and talk to other windows with `postMessage`. `async`/`await` write asynchronous steps (waiting for
a network answer) in a straight line.

## Why this repository uses it

Hosted fields need a little code in the customer's browser: the merchant's page asks its server for a payment, then hands over to the
provider's script, which opens the provider's card frame and tells it to confirm. The two scripts show exactly where the card does and does not go. They are
short strings inside Python files; **the project does not run JavaScript in its tests**, the scripted browser makes the requests the
scripts would make (and a one-off check of the real scripts in a browser was recorded in an early commit).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/interfaces/merchant_app.py` | `CHECKOUT_JS`: served at `/static/checkout.js`. |
| `src/pci_scope/interfaces/provider_app.py` | `ELEMENTS_JS` (the provider's script) and the script inside `FRAME_HTML`. |

## How it works underneath

The browser downloads the script and runs it in the page's context. `fetch(url, options)` returns a promise of a response. `await`
pauses until the promise is ready. `postMessage(data, origin)` sends a message to another window, but only delivers it if that window is
from the named origin; the receiver checks `event.origin` before trusting it. `document.currentScript` is the `<script>` element being run;
`dataset.key` reads its `data-key` attribute.

## Walkthrough of this repository's use

`src/pci_scope/interfaces/merchant_app.py`:

```python
CHECKOUT_JS = """\
(async function () {
  var key = document.currentScript.dataset.key;
  var provider = Provider(key);
  var started = await (await fetch("/create-payment", { method: "POST" })).json();
  var elements = provider.elements({ clientSecret: started.clientSecret });
  elements.create("payment").mount("#card");
  document.querySelector("#pay").onclick = function () {
    provider.confirmPayment({ elements: elements, confirmParams: { return_url: location.origin + "/done" } });
  };
})();
"""
```

- `(async function () { ... })();` is an **immediately invoked** async function: it runs at once and keeps its variables private.
- `document.currentScript.dataset.key` reads the publishable key from the script tag.
- `Provider(key)` is the function the provider's script defined.
- `await (await fetch("/create-payment", { method: "POST" })).json()` asks the merchant's server for a payment and parses the JSON answer: a client
  secret and an id. No card is involved.
- `provider.elements(...).create("payment").mount("#card")` asks the provider's script to put its frame into the `<div id="card">`.
- On a click, `provider.confirmPayment(...)` asks the frame to confirm and names the page to return to.

`src/pci_scope/interfaces/provider_app.py`:

```python
ELEMENTS_JS = """\
// The provider's script. It runs in the merchant's page, creates an iframe served by the provider, and asks that frame
// to confirm the payment. The card is typed into the frame, so the merchant's page and server never see it.
(function () {
  var origin = new URL(document.currentScript.src).origin;
  window.Provider = function (publishableKey) {
    return {
      elements: function (options) {
        var frame = null;
        return {
          create: function () {
            return {
              mount: function (selector) {
                frame = document.createElement("iframe");
                frame.title = "Card details";
                frame.style.cssText = "border:0;width:100%;height:150px";
                frame.src = origin + "/frame?origin=" + encodeURIComponent(location.origin) +
                  "&client_secret=" + encodeURIComponent(options.clientSecret);
                document.querySelector(selector).appendChild(frame);
              },
            };
          },
          frame: function () { return frame; },
        };
      },
      confirmPayment: function (args) {
        var frame = args.elements.frame();
        window.addEventListener("message", function (event) {
          if (event.origin !== origin) { return; }
          if (event.data.status === "succeeded") {
            location.href = args.confirmParams.return_url + "?payment_intent=" + encodeURIComponent(event.data.id);
          } else {
            document.querySelector("#message").textContent = event.data.message || "The payment did not go through.";
          }
        });
        frame.contentWindow.postMessage({ type: "confirm" }, origin);
      },
    };
  };
})();
"""
```

The provider's script runs **in the merchant's page**. `new URL(document.currentScript.src).origin` finds the provider's own origin.
`mount` creates an `<iframe>` whose address is the provider's `/frame`, so the card inputs belong to the provider. `confirmPayment` sends
`postMessage({ type: "confirm" }, origin)` to the frame, and listens for the answer: `if (event.origin !== origin) { return; }` ignores
messages from anywhere else, and on `succeeded` the page navigates to the merchant's `/done?payment_intent=...`.

`src/pci_scope/interfaces/provider_app.py`:

```python
  window.addEventListener("message", async function (event) {
    if (!event.data || event.data.type !== "confirm") { return; }
    var parts = document.getElementById("expiry").value.split("/").map(function (p) { return p.trim(); });
    var headers = { "Content-Type": "application/x-www-form-urlencoded", "X-Publishable-Key": key };
    var method = await (await fetch("/v1/payment_methods", { method: "POST", headers: headers, body: form({
      "card[number]": document.getElementById("number").value,
      "card[exp_month]": parts[0] || "", "card[exp_year]": parts[1] || "",
      "card[cvc]": document.getElementById("cvc").value }) })).json();
    if (method.error) { parent.postMessage({ status: "failed", message: method.error.message }, event.origin); return; }
    var result = await (await fetch("/v1/payment_intents/" + intentId + "/confirm", { method: "POST", headers: headers,
      body: form({ client_secret: secret, payment_method: method.id }) })).json();
    parent.postMessage(
      result.error ? { status: "failed", message: result.error.message } : { status: result.status, id: result.id },
      event.origin);
  });
```

Inside the frame (the provider's origin): when it is told to confirm, it reads the three inputs, `fetch`es the provider's own `/v1/payment_methods`
(**the card goes to the provider**), then confirms the payment and reports the result to the parent page with `parent.postMessage(...)`.
`new URLSearchParams(values).toString()` builds the form body.

## Try it yourself

```bash
.venv/bin/python -c "from pci_scope.interfaces.merchant_app import CHECKOUT_JS; print(CHECKOUT_JS)"
```
Prints the merchant's script.

```bash
.venv/bin/python -c "from pci_scope.interfaces.merchant_app import CHECKOUT_JS; print('card' in CHECKOUT_JS.lower(), 'number' in CHECKOUT_JS.lower())"
```
Prints `True False`: the word "card" appears only as the target `#card` and a heading; no card number is handled.

```bash
.venv/bin/python -c "from pci_scope.interfaces.provider_app import ELEMENTS_JS; print(ELEMENTS_JS.count('postMessage'), 'event.origin !== origin' in ELEMENTS_JS)"
```
Prints `1 True`: one message sent, origin checked on receive.

```bash
ls package.json 2>&1 | head -1
```
Prints `ls: package.json: No such file or directory` (on Linux, `ls: cannot access 'package.json': ...`): this is not a Node project, and no JavaScript tool is needed.

## Mistakes people make

- **Not checking `event.origin`** in a `message` listener, so any page can send commands.
- **Sending `postMessage` with `"*"` as the target** when the data matters. The scripts name the exact origin.
- **Putting secrets in a script.** The page holds only the publishable key.
- **Assuming the scripts were run by the tests.** They were not; the scripted browser mimics their requests.

## Check yourself

1. What does `await` do?
   **Answer:** Pauses an async function until a promise (such as a network answer) is ready.
2. Why does the receiver check `event.origin`?
   **Answer:** So only the expected window can send it commands.
3. Where does the card number go when typed?
   **Answer:** Into the provider's iframe, then to the provider's `/v1/payment_methods`.
4. What does `document.currentScript` refer to?
   **Answer:** The `<script>` element that is running.
5. Does the test suite execute these scripts?
   **Answer:** No; the scripted browser makes the same requests.

## Further reading

- MDN, JavaScript guide: <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide>
- `fetch`: <https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API>
- `postMessage`: <https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage>
