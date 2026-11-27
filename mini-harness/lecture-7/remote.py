"""本地 HTTP 入口。把同一份清单映射成 endpoint，处理一次 POST。

对应上游：Connection 独占 route 与信封，网关只认领 endpoint 并调用。
这里不把 request 对象交给业务函数，只用它的 body 构造参数。
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from harness_core import Harness, dispatch


def make_handler(harness):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/invoke":
                self.send_error(404, "unknown route")
                return

            length = int(self.headers.get("Content-Length", 0))
            try:
                envelope = json.loads(self.rfile.read(length).decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                envelope = {}

            reply = dispatch(harness, envelope)
            body = json.dumps(reply, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass

    return Handler


def start_server(harness=None):
    harness = harness or Harness()
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(harness))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
