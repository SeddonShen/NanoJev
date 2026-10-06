#!/usr/bin/env python3
"""Model arena: one page comparing all deployed NanoJev checkpoints.

Fans a chosen dataset probe (or custom JSON) out to the local serve_decisions
instances concurrently and returns each model's probability distribution.

Usage: venv/bin/python dashboard/model_arena.py --port 8820
"""
import argparse
import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
DEV = ROOT / "data/NanoJev-unified/unified/hard/dev.jsonl"

MODELS = [
    {"name": "hard_lr1e5 ×4800", "port": 8810, "color": "#4f8ef7", "tag": "ours"},
    {"name": "hard_lr2e5 ×4800", "port": 8813, "color": "#f7944f", "tag": "ours"},
    {"name": "soft_lr1e5 ×4800", "port": 8815, "color": "#4ff7a0", "tag": "ours"},
    {"name": "soft_lr2e5 ×4800", "port": 8817, "color": "#f76fb0", "tag": "ours"},
    {"name": "官方发布 (hard_lr1e5@400)", "port": 8819, "color": "#c9a227", "tag": "official"},
]
PROBES_PER_TASK = 8


def build_probes():
    rows = [json.loads(l) for l in DEV.open(encoding="utf-8") if l.strip()]
    by_task, picked = {}, {"maze": [], "snake": [], "shooting_basic": [], "shooting_predict_position": []}
    for row in rows:
        meta = row["metadata"]
        task = (f"{meta['task']}_{meta['spec']['scenario']}" if meta["task"] == "shooting" else meta["task"])
        if task not in picked:
            continue
        ep = meta.get("episode_id") or row["state_id"]
        if any(p["episode"] == ep for p in picked[task]):
            continue  # one step per episode for variety
        qid, q = next(iter(row["questions"].items()))
        target = None
        if row.get("teacher") and qid in (row["teacher"].get("native_probs") or {}):
            target = {"kind": "Jev 分布", "probs": row["teacher"]["native_probs"][qid]}
        elif row.get("gold") and qid in row["gold"]:
            target = {"kind": "专家动作", "gold": row["gold"][qid]}
        picked[task].append({
            "task": task, "episode": ep, "qid": qid,
            "label": f"{ep[:10]}… 决策#{meta.get('decision_index', 0)}",
            "state": row["state"], "question": q,
            "target": target,
            "executed": meta.get("executed_action") if isinstance(meta.get("executed_action"), str) else None,
        })
    return {task: items[:PROBES_PER_TASK] for task, items in picked.items() if items}


def query_model(port, payload, out, name):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/evaluate", data=body,
                                 headers={"Content-Type": "application/json"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        answers = {}
        for st in data.get("states", []):
            for qid, ans in (st.get("answers") or {}).items():
                answers[qid] = ans.get("probabilities", ans)
        out[name] = {"ok": True, "latency_ms": round((time.perf_counter() - started) * 1000),
                     "answers": answers}
    except Exception as exc:
        out[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


class Handler(BaseHTTPRequestHandler):
    probes = None

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html", "/arena"):
            self._send(200, (HERE / "model_arena.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/models":
            self._send(200, json.dumps(MODELS, ensure_ascii=False).encode())
        elif self.path == "/api/probes":
            self._send(200, json.dumps(self.probes, ensure_ascii=False).encode())
        else:
            self._send(404, b"not found")

    def do_POST(self):
        if self.path != "/api/compare":
            self._send(404, b"not found")
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        state, question = payload.get("state"), payload.get("question")
        if not isinstance(state, str) or not isinstance(question, dict):
            self._send(400, json.dumps({"error": "need {state, question}"}).encode())
            return
        request = {"states": [{"id": "arena", "state": state, "questions": {"q0": question}}]}
        results, threads = {}, []
        for model in MODELS:
            t = threading.Thread(target=query_model, args=(model["port"], request, results, model["name"]))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        for model in MODELS:  # keep model order even on error
            results.setdefault(model["name"], {"ok": False, "error": "no response"})
        self._send(200, json.dumps({"models": results}, ensure_ascii=False).encode())

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8820)
    args = ap.parse_args()
    Handler.probes = build_probes()
    print(f"model arena: http://127.0.0.1:{args.port}  ({len(MODELS)} models, "
          f"{sum(len(v) for v in Handler.probes.values())} probes)")
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
