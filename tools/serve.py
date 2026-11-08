#!/usr/bin/env python3
"""Servidor local que imita a Cloudflare (URLs sem .html, pastas com index.html, 404.html).
Uso: python3 tools/serve.py [porta]"""
import http.server, sys, os
from pathlib import Path
PUB = Path(__file__).resolve().parent.parent / "public"

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(PUB), **k)
    def log_message(self, *a): pass
    def send_head(self):
        path = self.path.split("?")[0].split("#")[0]
        f = PUB / path.lstrip("/")
        if not path.endswith("/") and (PUB / (path.lstrip("/") + ".html")).exists():
            self.path = path + ".html"
        elif not f.exists() and not (f.is_dir()):
            self.path = "/404.html"
            r = super().send_head()
            return r
        return super().send_head()

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8791
http.server.ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
