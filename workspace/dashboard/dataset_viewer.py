#!/usr/bin/env python3
"""Serve the dataset viewer page + episodes.json. Stdlib only.

Usage: venv/bin/python dashboard/dataset_viewer.py --port 8800
Rebuilds static/episodes.json first (see build_dataset_views.py).
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html", "/viewer"):
            body, ctype = (HERE / "dataset_viewer.html").read_bytes(), "text/html; charset=utf-8"
        elif self.path == "/data/episodes.json":
            body, ctype = (HERE / "static/episodes.json").read_bytes(), "application/json"
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    import build_dataset_views
    build_dataset_views.main(build_dataset_views.ROOT / "data/NanoJev-unified/unified/hard/dev.jsonl")
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8800)
    args = ap.parse_args()
    print(f"dataset viewer: http://127.0.0.1:{args.port}")
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
