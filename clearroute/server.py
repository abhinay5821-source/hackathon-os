"""Local authenticated reviewer endpoint for an arranged screen-share."""
from __future__ import annotations
import argparse, hmac, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .decision import record_decision
from .review import render_review

MAX_BODY_BYTES = 16_384

def make_handler(result_path: Path, decision_path: Path, token: str):
    if not token:
        raise ValueError("a non-empty review token is required")
    result_path, decision_path = result_path.resolve(), decision_path.resolve()
    class ReviewHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args): return
        def _authorized(self):
            return hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {token}")
        def _send(self, status, body, content_type):
            self.send_response(status)
            for key, value in (("Content-Type", content_type), ("Content-Length", str(len(body))), ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")):
                self.send_header(key, value)
            self.end_headers(); self.wfile.write(body)
        def _json(self, status, payload):
            self._send(status, json.dumps(payload).encode(), "application/json")
        def _require_auth(self):
            if self._authorized(): return True
            self._json(401, {"error": "unauthorized"}); return False
        def do_GET(self):
            if not self._require_auth(): return
            if self.path != "/review": self._json(404, {"error": "not_found"}); return
            try:
                result = json.loads(result_path.read_text(encoding="utf-8"))
                page = render_review(result, result_path.parent).encode()
            except (OSError, json.JSONDecodeError):
                self._json(500, {"error": "result_unavailable"}); return
            self._send(200, page, "text/html; charset=utf-8")
        def do_POST(self):
            if not self._require_auth(): return
            if self.path != "/decision": self._json(404, {"error": "not_found"}); return
            try: size = int(self.headers.get("Content-Length", "0"))
            except ValueError: self._json(400, {"error": "invalid_content_length"}); return
            if size <= 0 or size > MAX_BODY_BYTES:
                self._json(413, {"error": "invalid_body_size"}); return
            try:
                payload = json.loads(self.rfile.read(size))
                note = str(payload.get("note", ""))
                if len(note) > 500: raise ValueError("note_too_long")
                record = record_decision(result_path, decision_path, str(payload["decision"]), note)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                self._json(400, {"error": "invalid_decision"}); return
            self._json(201, record)
    return ReviewHandler

def main():
    parser = argparse.ArgumentParser(description="Run the local ClearRoute review endpoint")
    parser.add_argument("result", type=Path)
    parser.add_argument("--decision-output", type=Path, default=Path("clearroute-decision.json"))
    parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(args.result, args.decision_output, os.environ.get("CLEARROUTE_REVIEW_TOKEN", "")))
    print(f"ClearRoute reviewer listening on http://{args.host}:{args.port}/review")
    server.serve_forever()

if __name__ == "__main__": main()
