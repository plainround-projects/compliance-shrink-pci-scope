"""The "before": the lesson's naive checkout. It posts card details to its own server and logs the whole form.

This app exists to be scanned and measured. Do not run it with anything but the provider's published test card.
"""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, request

FORM = """<form method="post" action="/pay">
  Card <input name="card_number"> Expiry <input name="expiry"> CVV <input name="cvv">
  <button>Pay 19.00</button></form>"""


def create_naive_app(log_path: Path) -> Flask:
    """The naive app, logging requests to `log_path`."""
    app = Flask(__name__)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger = logging.getLogger(f"naive.{log_path}")
    logger.setLevel(logging.INFO)
    logger.handlers[:] = [handler]
    logger.propagate = False

    @app.get("/")
    def checkout() -> str:
        return FORM

    @app.post("/pay")
    def pay() -> str:
        logger.info("payment request: %s", dict(request.form))  # the mistake: card data reaches the log
        return "paid (simulated)"

    return app
