"""Minimal, purpose-built Updater-Service (Section 9.10 / 20 of the
design doc).

This runs as its own container with the least privilege necessary to
manage the SchoolPrint Podman Compose project (a Podman socket mount),
completely separate from the backend container's own permissions. It
exposes exactly one action over HTTP, reachable only on the internal
Compose network: `POST /run` triggers `scripts/updater-trigger.sh`
(`podman-compose pull` + `podman-compose up -d`) and returns the
combined output.

Deliberately dependency-free (Python stdlib only) to keep this
component's own attack surface as small as possible.
"""

from __future__ import annotations

import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SCRIPT_PATH = os.environ.get(
    "SCHOOLPRINT_UPDATER_SCRIPT", "/opt/schoolprint/scripts/updater-trigger.sh"
)
TIMEOUT_SECONDS = int(os.environ.get("SCHOOLPRINT_UPDATER_TIMEOUT", "600"))
PORT = int(os.environ.get("PORT", "8090"))


def run_update() -> tuple[int, str]:
    try:
        result = subprocess.run(  # noqa: S603 - fixed single-element args list, no shell
            [SCRIPT_PATH],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return 127, f"Updater script not found at {SCRIPT_PATH}"
    except subprocess.TimeoutExpired:
        return 124, f"Updater script did not finish within {TIMEOUT_SECONDS}s"

    log = result.stdout
    if result.stderr:
        log = f"{log}\n--- stderr ---\n{result.stderr}"
    return result.returncode, log.strip()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - required http.server signature
        if self.path != "/run":
            self.send_response(404)
            self.end_headers()
            return
        returncode, log = run_update()
        body = json.dumps({"returncode": returncode, "log": log}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required http.server signature
        if self.path != "/healthz":
            self.send_response(404)
            self.end_headers()
            return
        body = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_str: str, *args: object) -> None:  # noqa: A002
        pass


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
