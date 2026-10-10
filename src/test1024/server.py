"""Loopback-only HTTP service; the CLI sends every operation to this process."""

import json
import logging
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import ConfigError, server_config
from .db import Accounts

USERNAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,31}\Z")


def make_handler(accounts):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, payload):
            try:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                logging.warning("client disconnected before response was sent")

        def do_GET(self):
            if self.path == "/health":
                self.respond(200, {"status": "running"})
            else:
                self.respond(404, {"error": "not found"})

        def do_POST(self):
            if self.path not in ("/create", "/exists", "/login"):
                self.respond(404, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 4096:
                    raise ValueError("invalid request size")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("request body must be a JSON object")
                username = data.get("username", "")
                if not isinstance(username, str) or not USERNAME.fullmatch(username):
                    raise ValueError("username must be 1-32 ASCII letters, digits or underscores")
                if self.path != "/exists":
                    password = data.get("password", "")
                    if not isinstance(password, str) or not 1 <= len(password) <= 256:
                        raise ValueError("password must be 1-256 characters")
                if self.path == "/create":
                    result = {"created": accounts.create(username, password)}
                elif self.path == "/exists":
                    result = {"exists": accounts.exists(username)}
                else:
                    result = {"result": accounts.login(username, password)}
                self.respond(200, result)
            except (ValueError, TypeError) as exc:
                self.respond(400, {"error": str(exc)})
            except Exception:
                logging.exception("request failed")
                self.respond(500, {"error": "database operation failed"})

        def log_message(self, fmt, *args):
            logging.info("%s - %s", self.address_string(), fmt % args)

    return Handler


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        config = server_config()
        accounts = Accounts(config)
        accounts.check()
    except Exception as exc:
        logging.error("startup failed: %s", exc)
        return 1
    try:
        with ThreadingHTTPServer(("127.0.0.1", config["app_port"]), make_handler(accounts)) as server:
            logging.info("1024test listening on 127.0.0.1:%s", config["app_port"])
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                logging.info("shutdown requested")
    except OSError:
        logging.exception("could not bind 127.0.0.1:%s", config["app_port"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
