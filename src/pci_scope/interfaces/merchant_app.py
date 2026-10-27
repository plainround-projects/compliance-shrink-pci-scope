"""The merchant's web app after the redesign: it serves the page, creates the payment, asks the provider the result.

There is no route that accepts a card number. A request body is never logged.
"""

from __future__ import annotations

import logging
import time

from flask import Flask, Response, jsonify, request

from pci_scope.application.checkout import CheckoutService
from pci_scope.domain.payment import Order, PaymentError

logger = logging.getLogger("merchant")

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


def _order_json(order: Order) -> dict[str, object]:
    return {
        "id": order.id,
        "payment_intent": order.payment_intent_id,
        "status": order.status,
        "amount": order.amount_cents,
        "currency": order.currency,
    }


def create_merchant_app(checkout: CheckoutService, provider_base_url: str, publishable_key: str) -> Flask:
    """The merchant's routes. The page's content security policy names the provider and nothing else."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    policy = (
        f"default-src 'self'; script-src 'self' {provider_base_url}; frame-src {provider_base_url}; "
        f"connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    )

    @app.after_request
    def secure(response: Response) -> Response:
        response.headers["Content-Security-Policy"] = policy
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/healthz")
    def healthz() -> Response:
        return jsonify(status="ok")

    @app.get("/")
    def page() -> Response:
        return Response(
            PAGE.replace("__PROVIDER__", provider_base_url).replace("__KEY__", publishable_key), mimetype="text/html"
        )

    @app.get("/static/checkout.js")
    def script() -> Response:
        return Response(CHECKOUT_JS, mimetype="text/javascript")

    @app.post("/create-payment")
    def create_payment() -> Response:
        started = checkout.start()
        logger.info("created payment %s amount=1900 eur", started.intent_id)
        return jsonify(clientSecret=started.client_secret, id=started.intent_id)

    @app.get("/done")
    def done() -> tuple[str, int]:
        order = checkout.complete(request.args.get("payment_intent", ""))
        logger.info("payment %s status=%s", order.payment_intent_id, order.status)
        return (f"payment {order.payment_intent_id}: {order.status}", 200 if order.status == "succeeded" else 402)

    @app.post("/charge-again")
    def charge_again() -> Response:
        order = checkout.charge_again((request.get_json(silent=True) or {}).get("payment_intent", ""))
        logger.info("repeat charge %s status=%s", order.payment_intent_id, order.status)
        return jsonify(_order_json(order))

    @app.post("/refund")
    def refund() -> Response:
        intent = (request.get_json(silent=True) or {}).get("payment_intent", "")
        refund_id = checkout.refund(intent)
        logger.info("refunded %s as %s", intent, refund_id)
        return jsonify(refund=refund_id, payment_intent=intent)

    @app.post("/webhook")
    def webhook() -> Response:
        outcome = checkout.handle_event(request.get_data(), request.headers.get("Provider-Signature"), int(time.time()))
        logger.info("webhook %s", outcome)
        return jsonify(outcome=outcome)

    @app.errorhandler(PaymentError)
    def payment_failed(problem: PaymentError) -> tuple[Response, int]:
        logger.warning("payment error: %s", problem)
        return jsonify(error=str(problem)), 402

    @app.errorhandler(404)
    def not_found(_: Exception) -> tuple[Response, int]:
        return jsonify(error="not found"), 404

    @app.errorhandler(413)
    def too_large(_: Exception) -> tuple[Response, int]:
        return jsonify(error="request too large"), 413

    @app.errorhandler(Exception)
    def unexpected(problem: Exception) -> tuple[Response, int]:
        logger.error("unhandled %s", type(problem).__name__)
        return jsonify(error="internal error"), 500

    return app
