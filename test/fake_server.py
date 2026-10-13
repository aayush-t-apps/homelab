"""A stand-in for ntfy and the camera, for test/run.

  GET /snapshot   the bytes of <dir>/snapshot, or 503 when it's missing (a camera that doesn't answer)
  anything else   an alarm: recorded as one JSON line in <dir>/requests.jsonl; answers 200, or the
                  status in <dir>/status with an ntfy-style error when that file exists
"""
import json
import pathlib
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

port, folder = int(sys.argv[1]), pathlib.Path(sys.argv[2])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def answer(self, code, body, kind="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def alarm(self):
        url = urlsplit(self.path)
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        record = {
            "method": self.command,
            "path": url.path,
            "query": dict(parse_qsl(url.query)),
            "body_len": len(body),
            "body": body.decode("utf-8", "replace") if len(body) < 2000 else "",
        }
        with open(folder / "requests.jsonl", "a") as f:
            f.write(json.dumps(record) + "\n")
        status = folder / "status"
        if status.exists():
            code = int(status.read_text())
            self.answer(code, json.dumps({"code": code * 100 + 1, "http": code, "error": "limit reached"}).encode())
        else:
            self.answer(200, json.dumps({"id": "x", "topic": url.path.strip("/")}).encode())

    def do_GET(self):
        if self.path.startswith("/snapshot"):
            snap = folder / "snapshot"
            if snap.exists():
                self.answer(200, snap.read_bytes(), "image/jpeg")
            else:
                self.answer(503, b"{}")
        else:
            self.alarm()

    do_POST = do_PUT = alarm


ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
