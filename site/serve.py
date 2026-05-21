#!/usr/bin/env python3
"""HTTPS dev server for the marketing/app site."""
import ssl
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).parent / "root/var/www/ponderosafireprotection.com/html"
CERT = Path(__file__).parent / "dev-cert.pem"
KEY  = Path(__file__).parent / "dev-key.pem"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print(f"[site] {self.address_string()} - {fmt % args}")


ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(CERT, KEY)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.socket = ctx.wrap_socket(server.socket, server_side=True)
print(f"Serving https://0.0.0.0:{PORT}  (root: {ROOT})")
server.serve_forever()
