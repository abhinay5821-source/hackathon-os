"""Local JSON HTTP boundary for the fictional PrivacyGate fixture."""
from __future__ import annotations
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .core import AccessDenied, Actor, RecordService, fictional_records

def make_handler(service: RecordService):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parts = urlparse(self.path).path.strip("/").split("/")
            if len(parts) != 2 or parts[0] != "records":
                return self._json(404, {"error": "not_found"})
            actor_id = self.headers.get("X-Actor-Id", "").strip()
            role = self.headers.get("X-Actor-Role", "").strip()
            if not actor_id or role not in {"student", "guardian", "teacher", "principal"}:
                return self._json(401, {"error": "actor_headers_required"})
            try:
                record = service.read(Actor(actor_id, role), parts[1])
            except AccessDenied:
                return self._json(403, {"error": "forbidden"})
            except KeyError:
                return self._json(404, {"error": "record_not_found"})
            self._json(200, {"record": record, "fixture": "fictional-only"})

        def _json(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format, *_args):
            return
    return Handler

def main() -> None:
    parser = argparse.ArgumentParser(description="Serve fictional PrivacyGate records locally")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(RecordService(fictional_records())))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
