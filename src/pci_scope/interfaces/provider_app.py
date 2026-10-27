"""A local stand-in for a payment provider's test mode: the same shape of API as a real one, with hosted fields.

The card form is served from this origin, in an iframe. The merchant's page loads only a script and the iframe from
here; the card number goes from the customer's browser to this app and never to the merchant. State is in memory.
"""

from __future__ import annotations

import contextlib
import json
import secrets
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from flask import Flask, Response, jsonify, request

from pci_scope.domain.card import DECLINED_TEST_CARD, luhn_valid
from pci_scope.domain.webhook import sign

Deliver = Callable[[str, bytes, str], None]


def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(12)}"


def deliver_over_http(url: str, body: bytes, signature: str) -> None:
    """POST a webhook with a timeout; a failure is logged by the caller, never raised into the payment."""
    http = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/json", "Provider-Signature": signature}
    )
    with urllib.request.urlopen(http, timeout=5):
        pass


@dataclass
class ProviderState:
    """Everything the provider holds. A real one holds the card; this one keeps only brand and last four digits."""

    secret_key: str
    publishable_key: str
    webhook_secret: str
    webhook_url: str
    deliver: Deliver = deliver_over_http
    intents: dict[str, dict[str, Any]] = field(default_factory=dict)
    methods: dict[str, dict[str, Any]] = field(default_factory=dict)
    customers: set[str] = field(default_factory=set)
    refunds: dict[str, str] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)


def _public(intent: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in intent.items() if key not in ("confirmed_with",)}


def create_provider_app(state: ProviderState) -> Flask:
    """The provider's API, its script and its hosted card form."""
    app = Flask(__name__)

    def error(status: int, kind: str, message: str) -> tuple[Response, int]:
        return jsonify(error={"type": kind, "message": message}), status

    def secret_ok() -> bool:
        return request.headers.get("Authorization", "") == f"Bearer {state.secret_key}"

    def publishable_ok() -> bool:
        return (request.headers.get("X-Publishable-Key") or request.form.get("key", "")) == state.publishable_key

    def emit(kind: str, intent: dict[str, Any]) -> None:
        event = {"id": _id("evt"), "type": kind, "data": {"object": _public(intent)}}
        state.events.append(event)
        body = json.dumps(event).encode()
        # If the merchant is down the event is lost; a real provider retries for days.
        with contextlib.suppress(urllib.error.URLError, OSError, TimeoutError):
            state.deliver(state.webhook_url, body, sign(state.webhook_secret, body, int(time.time())))

    @app.get("/healthz")
    def healthz() -> Response:
        return jsonify(status="ok")

    @app.get("/v1/elements.js")
    def elements_js() -> Response:
        return Response(ELEMENTS_JS, mimetype="text/javascript")

    @app.get("/frame")
    def frame() -> Response:
        origin = request.args.get("origin", "")
        page = FRAME_HTML.replace("__KEY__", state.publishable_key).replace(
            "__SECRET__", request.args.get("client_secret", "").replace('"', "")
        )
        response = Response(page, mimetype="text/html")
        response.headers["Content-Security-Policy"] = (
            f"frame-ancestors {origin or 'none'}; default-src 'self'; script-src 'self' 'unsafe-inline'"
        )
        return response

    @app.post("/v1/customers")
    def create_customer() -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        customer = _id("cus")
        state.customers.add(customer)
        return jsonify(id=customer)

    @app.post("/v1/payment_methods")
    def create_method() -> tuple[Response, int] | Response:
        if not publishable_ok():
            return error(401, "authentication_error", "Invalid publishable key")
        number = request.form.get("card[number]", "").replace(" ", "")
        if not luhn_valid(number) or not request.form.get("card[cvc]"):
            return error(400, "card_error", "Your card number is incorrect.")
        method = _id("pm")
        state.methods[method] = {"brand": "visa", "last4": number[-4:], "decline": number == DECLINED_TEST_CARD}
        return jsonify(id=method, card={"brand": "visa", "last4": number[-4:]})

    @app.post("/v1/payment_intents")
    def create_intent() -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        form = request.form
        if not form.get("amount", "").isdigit() or not form.get("currency"):
            return error(400, "invalid_request_error", "amount and currency are required")
        intent_id = _id("pi")
        intent: dict[str, Any] = {
            "id": intent_id,
            "client_secret": f"{intent_id}_secret_{secrets.token_hex(8)}",
            "amount": int(form["amount"]),
            "currency": form["currency"],
            "customer": form.get("customer"),
            "payment_method": form.get("payment_method"),
            "status": "requires_payment_method", "setup_future_usage": form.get("setup_future_usage"),
        }  # fmt: skip
        with state.lock:
            state.intents[intent_id] = intent
            if form.get("confirm") == "true":
                method = state.methods.get(form.get("payment_method", ""))
                if method is None or form.get("customer") not in state.customers or form.get("off_session") != "true":
                    return error(
                        400,
                        "invalid_request_error",
                        "a saved payment method and customer are required to charge off-session",
                    )
                intent["status"] = "requires_payment_method" if method["decline"] else "succeeded"
                emit("payment_intent.payment_failed" if method["decline"] else "payment_intent.succeeded", intent)
        return jsonify(_public(intent))

    @app.get("/v1/payment_intents/<intent_id>")
    def get_intent(intent_id: str) -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        intent = state.intents.get(intent_id)
        return jsonify(_public(intent)) if intent else error(404, "invalid_request_error", "No such payment_intent")

    @app.post("/v1/payment_intents/<intent_id>/confirm")
    def confirm(intent_id: str) -> tuple[Response, int] | Response:
        if not publishable_ok():
            return error(401, "authentication_error", "Invalid publishable key")
        with state.lock:
            intent = state.intents.get(intent_id)
            if intent is None or intent["client_secret"] != request.form.get("client_secret"):
                return error(404, "invalid_request_error", "No such payment_intent")
            method = state.methods.get(request.form.get("payment_method", ""))
            if method is None:
                return error(400, "invalid_request_error", "payment_method is required")
            intent["payment_method"] = request.form["payment_method"]
            intent["status"] = "requires_payment_method" if method["decline"] else "succeeded"
            emit("payment_intent.payment_failed" if method["decline"] else "payment_intent.succeeded", intent)
            if method["decline"]:
                return error(402, "card_error", "Your card was declined.")
        return jsonify(_public(intent))

    @app.post("/v1/refunds")
    def refund() -> tuple[Response, int] | Response:
        if not secret_ok():
            return error(401, "authentication_error", "Invalid secret key")
        intent = state.intents.get(request.form.get("payment_intent", ""))
        if intent is None or intent["status"] != "succeeded":
            return error(400, "invalid_request_error", "only a succeeded payment can be refunded")
        refund_id = _id("re")
        state.refunds[refund_id] = intent["id"]
        return jsonify(id=refund_id, payment_intent=intent["id"])

    return app


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
  var key = "__KEY__", secret = "__SECRET__";
  var intentId = secret.split("_secret_")[0];
  function form(values) { return new URLSearchParams(values).toString(); }
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
</script>
"""
