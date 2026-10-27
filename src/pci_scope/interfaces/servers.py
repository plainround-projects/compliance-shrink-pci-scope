"""Run the three apps as real HTTP servers on local ports, in threads, and stop them cleanly."""

from __future__ import annotations

import logging
import socket
import threading
from types import TracebackType

from flask import Flask
from werkzeug.serving import BaseWSGIServer, make_server


def free_port() -> int:
    """A port nobody is listening on right now."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class LocalServer:
    """A Flask app served on 127.0.0.1:<port> until the context exits; shutdown waits for in-flight requests."""

    def __init__(self, app: Flask, port: int) -> None:
        logging.getLogger("werkzeug").setLevel(
            logging.WARNING
        )  # no access log: a URL is one more place for data to land
        self._server: BaseWSGIServer = make_server("127.0.0.1", port, app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self.url = f"http://127.0.0.1:{port}"

    def __enter__(self) -> LocalServer:
        self._thread.start()
        return self

    def __exit__(
        self, kind: type[BaseException] | None, value: BaseException | None, trace: TracebackType | None
    ) -> None:
        self._server.shutdown()
        self._thread.join(timeout=5)
        self._server.server_close()
